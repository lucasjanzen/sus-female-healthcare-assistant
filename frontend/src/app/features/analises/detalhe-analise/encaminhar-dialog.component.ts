import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

import { EncaminharRequest } from '../models/analise.model';

@Component({
  selector: 'app-encaminhar-dialog',
  standalone: true,
  imports: [ReactiveFormsModule, MatButtonModule, MatDialogModule, MatFormFieldModule, MatInputModule],
  template: `
    <h2 mat-dialog-title>Registrar encaminhamento</h2>
    <mat-dialog-content>
      <mat-form-field appearance="outline" style="width:100%; margin-top:8px">
        <mat-label>Observação (opcional)</mat-label>
        <textarea matInput [formControl]="observacaoCtrl" rows="4" placeholder="Descreva o encaminhamento..."></textarea>
      </mat-form-field>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>Cancelar</button>
      <button mat-raised-button color="primary" (click)="confirmar()">Confirmar encaminhamento</button>
    </mat-dialog-actions>
  `,
})
export class EncaminharDialogComponent {
  private readonly ref = inject(MatDialogRef<EncaminharDialogComponent>);
  private readonly fb = inject(FormBuilder);
  readonly observacaoCtrl = this.fb.nonNullable.control('');

  confirmar(): void {
    const dados: EncaminharRequest = { observacao: this.observacaoCtrl.value || undefined };
    this.ref.close(dados);
  }
}
