import { HttpErrorResponse } from '@angular/common/http';

export function extrairMensagemErro(err: HttpErrorResponse, fallback: string): string {
  const detail = err?.error?.detail;
  if (typeof detail === 'string') return detail;
  return fallback;
}
