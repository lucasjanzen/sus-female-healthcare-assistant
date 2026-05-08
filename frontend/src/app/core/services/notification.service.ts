import { Injectable, inject } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';

@Injectable({ providedIn: 'root' })
export class NotificationService {
  private readonly snackBar = inject(MatSnackBar);

  erro(msg: string, duration = 3000): void {
    this.snackBar.open(msg, 'Fechar', { duration });
  }

  sucesso(msg: string, duration = 3000): void {
    this.snackBar.open(msg, 'Fechar', { duration });
  }
}
