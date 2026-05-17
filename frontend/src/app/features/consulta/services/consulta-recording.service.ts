import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ConsultaRecordingService {
  private mediaRecorder: MediaRecorder | null = null;
  private mediaStream: MediaStream | null = null;
  private audioChunks: Blob[] = [];

  audioBlob: Blob | null = null;
  readonly gravando = signal(false);
  readonly gravacaoConcluida = signal(false);

  async iniciar(): Promise<void> {
    this.parar();
    this.audioBlob = null;
    this.audioChunks = [];
    this.gravacaoConcluida.set(false);

    this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });

    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : 'audio/ogg;codecs=opus';

    this.mediaRecorder = new MediaRecorder(this.mediaStream, { mimeType });

    this.mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) this.audioChunks.push(e.data);
    };

    this.mediaRecorder.onstop = () => {
      this.audioBlob = new Blob(this.audioChunks, { type: mimeType });
      this.gravacaoConcluida.set(true);
    };

    this.mediaRecorder.start(1000);
    this.gravando.set(true);
  }

  parar(): void {
    this.mediaRecorder?.stop();
    this.mediaStream?.getTracks().forEach((t) => t.stop());
    this.gravando.set(false);
  }

  limpar(): void {
    this.parar();
    this.audioBlob = null;
    this.audioChunks = [];
    this.gravacaoConcluida.set(false);
  }

  getAudioBlob(): Blob | null {
    return this.audioBlob;
  }

  setAudioBlob(blob: Blob): void {
    this.audioBlob = blob;
    this.gravacaoConcluida.set(true);
  }
}
