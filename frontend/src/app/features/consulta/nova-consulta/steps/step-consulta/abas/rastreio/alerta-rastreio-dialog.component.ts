import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-alerta-rastreio-dialog',
  standalone: true,
  imports: [MatDialogModule, MatButtonModule, MatIconModule],
  template: `
    <div style="padding: 24px;">
      <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
        <mat-icon [style]="'color: ' + corIcone + '; font-size: 32px; width: 32px; height: 32px;'">warning</mat-icon>
        <h2 mat-dialog-title style="margin: 0; font-size: 1.2rem;">{{ titulo }}</h2>
      </div>
      <mat-dialog-content>
        <p style="margin-bottom: 16px;">{{ texto }}</p>
        <div style="display: flex; flex-direction: column; gap: 8px;">
          @for (acao of acoes; track acao.label) {
            <button mat-stroked-button [color]="acao.color" style="justify-content: flex-start; text-align: left;">
              <mat-icon style="margin-right: 8px;">{{ acao.icon }}</mat-icon>
              {{ acao.label }}
            </button>
          }
        </div>
      </mat-dialog-content>
      <mat-dialog-actions align="end" style="margin-top: 16px;">
        <button mat-flat-button color="primary" (click)="fechar()">
          Registrar e continuar com acolhimento
        </button>
      </mat-dialog-actions>
    </div>
  `,
})
export class AlertaRastreioDialogComponent {
  titulo: string;
  texto: string;
  corIcone: string;
  acoes: Array<{ label: string; icon: string; color: string }>;

  constructor(
    public dialogRef: MatDialogRef<AlertaRastreioDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: { tipo: 'EPDS_ITEM_10' | 'HITS_FLAG' },
  ) {
    if (data.tipo === 'EPDS_ITEM_10') {
      this.titulo = 'Atenção — Risco Imediato';
      this.texto = 'A paciente indicou possibilidade de autolesão. É necessário acolhimento imediato e encaminhamento para serviço especializado.';
      this.corIcone = '#d32f2f';
      this.acoes = [
        { label: 'CAPS — Centro de Atenção Psicossocial', icon: 'local_hospital', color: 'warn' },
        { label: 'CVV — Centro de Valorização da Vida (188)', icon: 'phone', color: 'warn' },
        { label: 'Protocolo de Acolhimento em Saúde Mental', icon: 'article', color: '' },
      ];
    } else {
      this.titulo = 'Atenção — Indicativo de Violência Doméstica';
      this.texto = 'A pontuação do HITS está acima do ponto de corte (≥11), indicativo de situação de violência doméstica. Encaminhamento e acolhimento são necessários.';
      this.corIcone = '#e65100';
      this.acoes = [
        { label: 'CVR — Centro de Referência da Mulher', icon: 'support_agent', color: 'warn' },
        { label: 'Delegacia da Mulher', icon: 'local_police', color: '' },
        { label: 'Assistência Social', icon: 'people', color: '' },
      ];
    }
  }

  fechar(): void {
    this.dialogRef.close();
  }
}
