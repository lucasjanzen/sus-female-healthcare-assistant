import { Pipe, PipeTransform } from '@angular/core';
import { formatarDataBr } from '../../core/utils/date.utils';

@Pipe({ name: 'formatarData', standalone: true })
export class FormatDataPipe implements PipeTransform {
  transform(value: string | null | undefined): string {
    return value ? formatarDataBr(value) : '';
  }
}
