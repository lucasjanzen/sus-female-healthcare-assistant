import { Component } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-confirmar-encerramento-dialog',
  standalone: true,
  imports: [MatButtonModule, MatDialogModule, MatIconModule],
  template: `
    <h2 mat-dialog-title>Encerrar Consulta</h2>
    <mat-dialog-content>
      <p>Após encerrar, a consulta não poderá ser editada.</p>
      <p>Confirma o encerramento?</p>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>Cancelar</button>
      <button mat-flat-button color="warn" [mat-dialog-close]="true">
        <mat-icon>lock</mat-icon>
        Encerrar
      </button>
    </mat-dialog-actions>
  `,
})
export class ConfirmarEncerramentoDialogComponent {}
