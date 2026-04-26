import { NativeDateAdapter } from '@angular/material/core';

export class PtBrNativeDateAdapter extends NativeDateAdapter {
  override parse(value: unknown): Date | null {
    if (typeof value === 'string') {
      const trimmed = value.trim();
      const match = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(trimmed);

      if (match) {
        const day = Number(match[1]);
        const month = Number(match[2]) - 1;
        const year = Number(match[3]);
        const date = new Date(year, month, day);

        if (
          date.getFullYear() === year &&
          date.getMonth() === month &&
          date.getDate() === day
        ) {
          return date;
        }

        return null;
      }
    }

    return super.parse(value);
  }
}
