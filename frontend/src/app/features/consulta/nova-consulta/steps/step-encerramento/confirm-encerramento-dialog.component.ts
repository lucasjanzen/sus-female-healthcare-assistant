import { Component } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-confirm-encerramento-dialog',
  standalone: true,
  imports: [MatDialogModule, MatButtonModule, MatIconModule],
  template: `
    <h2 mat-dialog-title>Confirmar encerramento</h2>
    <mat-dialog-content>
      <p style="margin: 0; color: #555;">
        Após encerrar, a consulta <strong>não poderá ser editada</strong>.
        Esta ação é irreversível.
      </p>
    </mat-dialog-content>
    <mat-dialog-actions align="end" style="gap: 8px; padding: 16px;">
      <button mat-stroked-button (click)="fechar(false)">Cancelar</button>
      <button mat-flat-button color="warn" (click)="fechar(true)">
        <mat-icon style="margin-right: 4px; font-size: 18px; width: 18px; height: 18px;">lock</mat-icon>
        Encerrar
      </button>
    </mat-dialog-actions>
  `,
})
export class ConfirmEncerramentoDialogComponent {
  constructor(private ref: MatDialogRef<ConfirmEncerramentoDialogComponent>) {}

  fechar(confirmado: boolean): void {
    this.ref.close(confirmado);
  }
}
