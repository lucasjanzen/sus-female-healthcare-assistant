import { Component } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-confirmar-encerramento-atendimento-dialog',
  standalone: true,
  imports: [MatButtonModule, MatDialogModule, MatIconModule],
  template: `
    <h2 mat-dialog-title>Encerrar Consulta</h2>
    <mat-dialog-content>
      <p>
        Ao encerrar, a consulta será enviada automaticamente para análise de IA.
        Deseja continuar?
      </p>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button [mat-dialog-close]="false">Cancelar</button>
      <button mat-raised-button color="primary" [mat-dialog-close]="true">
        <mat-icon>check</mat-icon>
        Encerrar
      </button>
    </mat-dialog-actions>
  `,
})
export class ConfirmarEncerramentoAtendimentoDialogComponent {}
