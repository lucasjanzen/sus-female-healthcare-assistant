import { Component, computed, input } from '@angular/core';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatTableModule } from '@angular/material/table';

import { ConsultaAssumidaOut } from 'app/features/fila/models/fila.model';
import { HistoricoPesoItem } from 'app/features/consulta/services/historico.service';

interface LinhaPeso {
  pesoKg: number;
  registradoEm: string;
  variacaoTexto: string;
  variacaoCor: string;
}

@Component({
  selector: 'app-consulta-triagem',
  standalone: true,
  imports: [MatExpansionModule, MatTableModule],
  templateUrl: './consulta-triagem.component.html',
  styleUrl: './consulta-triagem.component.scss',
})
export class ConsultaTriagemComponent {
  readonly dadosConsulta = input<ConsultaAssumidaOut | null>(null);
  readonly historicoPeso = input<HistoricoPesoItem[]>([]);

  readonly colunasPeso = ['data', 'peso', 'variacao'];
  readonly linhasPeso = computed(() => this.mapearLinhas(this.historicoPeso()));
  readonly tendenciaPeso = computed(() => this.calcularTendencia(this.historicoPeso()));
  readonly tendenciaCor = computed(() => {
    switch (this.tendenciaPeso()) {
      case 'perda progressiva':  return '#c62828';
      case 'ganho progressivo':  return '#ef6c00';
      case 'variação irregular': return '#f9a825';
      default:                   return '#2e7d32';
    }
  });

  formatarDataPeso(iso: string): string {
    return new Date(iso).toLocaleDateString('pt-BR');
  }

  formatarPeso(kg: number): string {
    return kg.toFixed(1).replace('.', ',') + ' kg';
  }

  private mapearLinhas(hist: HistoricoPesoItem[]): LinhaPeso[] {
    return hist.map((item, i) => ({
      pesoKg: item.pesoKg,
      registradoEm: item.registradoEm,
      variacaoTexto: this.calcularVariacaoTexto(hist, i),
      variacaoCor: this.calcularVariacaoCor(hist, i),
    }));
  }

  private calcularVariacaoTexto(hist: HistoricoPesoItem[], index: number): string {
    if (index >= hist.length - 1) return '—';
    const diff = hist[index].pesoKg - hist[index + 1].pesoKg;
    if (diff === 0) return '—';
    const abs = Math.abs(diff).toFixed(1).replace('.', ',');
    return diff > 0 ? `▲ +${abs} kg` : `▼ −${abs} kg`;
  }

  private calcularVariacaoCor(hist: HistoricoPesoItem[], index: number): string {
    if (index >= hist.length - 1) return '';
    const diff = hist[index].pesoKg - hist[index + 1].pesoKg;
    if (diff > 5 || diff < -5) return '#b71c1c';
    if (diff > 2 || diff < -2) return '#e65100';
    return '';
  }

  private calcularTendencia(hist: HistoricoPesoItem[]): string {
    if (hist.length < 3) return '';
    const totalDiff = Math.abs(hist[0].pesoKg - hist[hist.length - 1].pesoKg);
    if (totalDiff < 1) return 'estável';
    let todosGanhos = true;
    let todasPerdas = true;
    for (let i = 0; i < hist.length - 1; i++) {
      const diff = hist[i].pesoKg - hist[i + 1].pesoKg;
      if (diff <= 0) todosGanhos = false;
      if (diff >= 0) todasPerdas = false;
    }
    if (todosGanhos) return 'ganho progressivo';
    if (todasPerdas) return 'perda progressiva';
    return 'variação irregular';
  }
}
