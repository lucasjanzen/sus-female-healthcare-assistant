import { Component, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import {
  MAT_DIALOG_DATA,
  MatDialogModule,
  MatDialogRef,
} from '@angular/material/dialog';
import { AlertaTriagem } from '../../../../../models/consulta.model';

export interface AlertasDialogData {
  alertas: AlertaTriagem[];
}

@Component({
  selector: 'app-alertas-dialog',
  standalone: true,
  imports: [MatDialogModule, MatButtonModule, MatChipsModule],
  template: `
    <h2 mat-dialog-title>Alertas críticos identificados</h2>
    <mat-dialog-content>
      <p style="margin-bottom: 12px; color: #555;">
        Os seguintes alertas foram gerados pela triagem. Revise antes de confirmar.
      </p>
      <div style="display: flex; flex-wrap: wrap; gap: 8px;">
        @for (alerta of data.alertas; track alerta.tipo) {
          <mat-chip style="background-color: #f44336; color: #fff;">
            {{ alerta.descricao }}
          </mat-chip>
        }
      </div>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-stroked-button (click)="dialogRef.close(false)">
        Revisar triagem
      </button>
      <button mat-raised-button color="warn" (click)="dialogRef.close(true)" style="margin-left: 8px;">
        Confirmar e enviar para fila
      </button>
    </mat-dialog-actions>
  `,
})
export class AlertasDialogComponent {
  readonly data = inject<AlertasDialogData>(MAT_DIALOG_DATA);
  readonly dialogRef = inject(MatDialogRef<AlertasDialogComponent>);
}
