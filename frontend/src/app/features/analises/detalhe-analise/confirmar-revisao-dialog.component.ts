import { Component } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule } from '@angular/material/dialog';

@Component({
  selector: 'app-confirmar-revisao-dialog',
  standalone: true,
  imports: [MatButtonModule, MatDialogModule],
  template: `
    <h2 mat-dialog-title>Revisar análise</h2>
    <mat-dialog-content>
      <p>Marcar esta análise como revisada sem encaminhamento?</p>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button [mat-dialog-close]="false">Cancelar</button>
      <button mat-raised-button [mat-dialog-close]="true">Confirmar</button>
    </mat-dialog-actions>
  `,
})
export class ConfirmarRevisaoDialogComponent {}
