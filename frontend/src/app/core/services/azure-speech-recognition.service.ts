import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, Observable, Subject, from, throwError } from 'rxjs';
import { catchError, switchMap, tap } from 'rxjs/operators';
import {
  AudioConfig,
  CancellationReason,
  ResultReason,
  SpeechConfig,
  SpeechRecognitionCanceledEventArgs,
  SpeechRecognitionEventArgs,
  SpeechRecognizer,
} from 'microsoft-cognitiveservices-speech-sdk';
import { environment } from 'environments/environment';

interface SpeechTokenResponse {
  token: string;
  region: string;
}

interface SpeechResult {
  /** 'partial' → frase sendo falada agora (ainda pode mudar). */
  type: 'partial' | 'final';
  text: string;
}

/**
 * Reconhecimento de voz contínuo via Azure Speech SDK.
 *
 * Fluxo seguro:
 *   1. Frontend busca token temporário em GET /speech/token (JWT obrigatório).
 *   2. SDK usa o token — a subscription key nunca sai do backend.
 *   3. Token é renovado automaticamente a cada 9 min (expira em 10 min).
 *   4. Ao destruir, recognizer é fechado corretamente para evitar vazamento.
 */
@Injectable({ providedIn: 'root' })
export class AzureSpeechRecognitionService {
  private readonly http = inject(HttpClient);
  private readonly tokenUrl = `${environment.apiUrl}/speech/token`;

  private recognizer: SpeechRecognizer | null = null;
  private speechConfig: SpeechConfig | null = null;
  // Guarda o timer de renovação para poder cancelá-lo
  private tokenRenewalTimer: ReturnType<typeof setTimeout> | null = null;

  private readonly _result$ = new Subject<SpeechResult>();
  private readonly _error$ = new Subject<string>();
  private readonly _listening$ = new BehaviorSubject<boolean>(false);

  /** Resultados parciais e finais de reconhecimento. */
  readonly result$ = this._result$.asObservable();
  /** Mensagens de erro do SDK ou do backend. */
  readonly error$ = this._error$.asObservable();
  /** true enquanto o microfone estiver ativo. */
  readonly listening$ = this._listening$.asObservable();

  private fetchToken(): Observable<SpeechTokenResponse> {
    return this.http.get<SpeechTokenResponse>(this.tokenUrl);
  }

  /**
   * Inicia reconhecimento contínuo.
   * Se já estiver ativo, retorna imediatamente sem criar nova instância.
   */
  iniciar(): Observable<void> {
    if (this.recognizer) {
      return from(Promise.resolve<void>(undefined));
    }

    return this.fetchToken().pipe(
      tap(({ token, region }) => {
        this._setupRecognizer(token, region);
        this._agendarRenovacaoToken();
      }),
      switchMap(
        () =>
          new Observable<void>((observer) => {
            this.recognizer!.startContinuousRecognitionAsync(
              () => {
                this._listening$.next(true);
                observer.next();
                observer.complete();
              },
              (err) => {
                this._listening$.next(false);
                observer.error(new Error(String(err)));
              },
            );
          }),
      ),
      catchError((err) => {
        this._error$.next(`Erro ao iniciar reconhecimento: ${err.message ?? err}`);
        return throwError(() => err);
      }),
    );
  }

  /**
   * Para o reconhecimento e libera o recognizer.
   * Retorna Promise para integração com código imperativo no componente.
   */
  parar(): Promise<void> {
    this._cancelarRenovacaoToken();
    if (!this.recognizer) return Promise.resolve();

    return new Promise((resolve) => {
      this.recognizer!.stopContinuousRecognitionAsync(
        () => {
          this._destruirRecognizer();
          this._listening$.next(false);
          resolve();
        },
        (err) => {
          // Resolve mesmo em erro para não bloquear o fluxo do componente
          console.error('Erro ao parar reconhecimento Azure Speech:', err);
          this._destruirRecognizer();
          this._listening$.next(false);
          resolve();
        },
      );
    });
  }

  /**
   * Destruição completa — deve ser chamado no ngOnDestroy do componente
   * para garantir que o microfone seja liberado e o socket fechado.
   */
  destroy(): void {
    this._cancelarRenovacaoToken();
    if (!this.recognizer) return;

    this.recognizer.stopContinuousRecognitionAsync(
      () => this._destruirRecognizer(),
      () => this._destruirRecognizer(),
    );
  }

  private _setupRecognizer(token: string, region: string): void {
    this.speechConfig = SpeechConfig.fromAuthorizationToken(token, region);
    this.speechConfig.speechRecognitionLanguage = 'pt-BR';

    const audioConfig = AudioConfig.fromDefaultMicrophoneInput();
    this.recognizer = new SpeechRecognizer(this.speechConfig, audioConfig);

    // Resultado parcial — texto sendo reconhecido enquanto a pessoa fala
    this.recognizer.recognizing = (_sender: unknown, event: SpeechRecognitionEventArgs) => {
      if (event.result.text) {
        this._result$.next({ type: 'partial', text: event.result.text });
      }
    };

    // Resultado final — frase completa reconhecida com alta confiança
    this.recognizer.recognized = (_sender: unknown, event: SpeechRecognitionEventArgs) => {
      if (event.result.reason === ResultReason.RecognizedSpeech && event.result.text) {
        this._result$.next({ type: 'final', text: event.result.text });
      }
    };

    // Sessão encerrada normalmente (ex: após parar())
    this.recognizer.sessionStopped = () => {
      this._listening$.next(false);
    };

    // Cancelamento por erro de rede, autenticação ou cotas
    this.recognizer.canceled = (_sender: unknown, event: SpeechRecognitionCanceledEventArgs) => {
      if (event.reason === CancellationReason.Error) {
        const msg = `Reconhecimento interrompido: ${event.errorDetails}`;
        console.error(msg);
        this._error$.next(msg);
      }
      this._listening$.next(false);
    };
  }

  // Tokens expiram em 10 min — renova com 1 min de folga para evitar falha silenciosa
  private _agendarRenovacaoToken(): void {
    this._cancelarRenovacaoToken();
    this.tokenRenewalTimer = setTimeout(() => this._renovarToken(), 9 * 60 * 1000);
  }

  private _renovarToken(): void {
    if (!this.speechConfig) return;

    this.fetchToken().subscribe({
      next: ({ token }) => {
        // Atualiza authorizationToken no config existente —
        // o SDK usa o novo valor nas próximas requisições sem reiniciar o recognizer
        this.speechConfig!.authorizationToken = token;
        this._agendarRenovacaoToken();
      },
      error: (err) => {
        console.error('Falha ao renovar token Azure Speech:', err);
        this._error$.next('Token de reconhecimento expirou e não foi possível renovar.');
      },
    });
  }

  private _cancelarRenovacaoToken(): void {
    if (this.tokenRenewalTimer !== null) {
      clearTimeout(this.tokenRenewalTimer);
      this.tokenRenewalTimer = null;
    }
  }

  private _destruirRecognizer(): void {
    if (this.recognizer) {
      try {
        this.recognizer.close();
      } catch {
        // Ignora erros ao fechar — o recognizer pode já estar fechado
      }
      this.recognizer = null;
    }
    this.speechConfig = null;
  }
}
