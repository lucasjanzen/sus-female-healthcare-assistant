import { Component, EventEmitter, Input, OnInit, Output, inject, signal } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { ExamesLabOut } from '../../../../../models/consulta.model';
import { ConsultaClinicaService } from '../../../../../services/consulta-clinica.service';

@Component({
  selector: 'app-exames-lab',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatFormFieldModule, MatInputModule, MatSelectModule,
    MatButtonModule, MatProgressSpinnerModule, MatSnackBarModule,
    MatExpansionModule,
  ],
  templateUrl: './exames-lab.component.html',
})
export class ExamesLabComponent implements OnInit {
  @Input() idConsulta!: string;
  @Output() salvo = new EventEmitter<ExamesLabOut>();

  private readonly fb = inject(FormBuilder);
  private readonly svc = inject(ConsultaClinicaService);
  private readonly snack = inject(MatSnackBar);

  readonly salvando = signal(false);
  readonly dadosSalvos = signal<ExamesLabOut | null>(null);

  form: FormGroup = this.fb.group({
      tipagemSanguinea: [null],
      hemogramaResultado: [null],
      hemogramaData: [null],
      vdrlResultado: [null],
      vdrlData: [null],
      glicemiaJejumResultado: [null],
      glicemiaJejumData: [null],
      totgResultado: [null],
      totgData: [null],
      urinalise: [null],
      uroculturaResultado: [null],
      hivStatus: [null],
      hivData: [null],
      hepatiteBStatus: [null],
      hepatiteBData: [null],
      hepatiteCStatus: [null],
      hepatiteCData: [null],
      toxoplasmoseStatus: [null],
      toxoplasmoseData: [null],
      usgData: [null],
      usgIgUsg: [null],
      usgBiometria: [null],
      usgPlacenta: [null],
  });

  ngOnInit(): void {
    this.svc.obterExamesLab(this.idConsulta).subscribe({
      next: (dados) => {
        this.dadosSalvos.set(dados);
        this._preencherForm(dados);
      },
      error: () => {},
    });
  }

  private _preencherForm(dados: ExamesLabOut): void {
    const h = dados.hemograma as Record<string, unknown> | undefined;
    const v = dados.vdrl as Record<string, unknown> | undefined;
    const g = dados.glicemiaJejum as Record<string, unknown> | undefined;
    const t = dados.totg as Record<string, unknown> | undefined;
    const hiv = dados.hiv as Record<string, unknown> | undefined;
    const hb = dados.hepatiteB as Record<string, unknown> | undefined;
    const hc = dados.hepatiteC as Record<string, unknown> | undefined;
    const tx = dados.toxoplasmose as Record<string, unknown> | undefined;
    const usg = dados.usgObstetrica as Record<string, unknown> | undefined;
    const ur = dados.urina as Record<string, unknown> | undefined;

    this.form.patchValue({
      tipagemSanguinea: dados.tipagemSanguinea,
      hemogramaResultado: h?.['resultado'],
      hemogramaData: h?.['dataColeta'],
      vdrlResultado: v?.['resultado'],
      vdrlData: v?.['dataColeta'],
      glicemiaJejumResultado: g?.['resultado'],
      glicemiaJejumData: g?.['dataColeta'],
      totgResultado: t?.['resultado'],
      totgData: t?.['dataColeta'],
      urinalise: ur?.['resultado'],
      uroculturaResultado: dados.urocultura,
      hivStatus: hiv?.['status'],
      hivData: hiv?.['dataColeta'],
      hepatiteBStatus: hb?.['status'],
      hepatiteBData: hb?.['dataColeta'],
      hepatiteCStatus: hc?.['status'],
      hepatiteCData: hc?.['dataColeta'],
      toxoplasmoseStatus: tx?.['status'],
      toxoplasmoseData: tx?.['dataColeta'],
      usgData: usg?.['data'],
      usgIgUsg: usg?.['igUsg'],
      usgBiometria: usg?.['biometria'],
      usgPlacenta: usg?.['placenta'],
    });
  }

  private _buildPayload(): Record<string, unknown> {
    const v = this.form.value;
    return {
      tipagemSanguinea: v.tipagemSanguinea || null,
      hemograma: v.hemogramaResultado ? { resultado: v.hemogramaResultado, dataColeta: v.hemogramaData } : null,
      vdrl: v.vdrlResultado ? { resultado: v.vdrlResultado, dataColeta: v.vdrlData } : null,
      glicemiaJejum: v.glicemiaJejumResultado ? { resultado: v.glicemiaJejumResultado, dataColeta: v.glicemiaJejumData } : null,
      totg: v.totgResultado ? { resultado: v.totgResultado, dataColeta: v.totgData } : null,
      urina: v.urinalise ? { resultado: v.urinalise } : null,
      urocultura: v.uroculturaResultado ? { resultado: v.uroculturaResultado } : null,
      hiv: v.hivStatus ? { status: v.hivStatus, dataColeta: v.hivData } : null,
      hepatiteB: v.hepatiteBStatus ? { status: v.hepatiteBStatus, dataColeta: v.hepatiteBData } : null,
      hepatiteC: v.hepatiteCStatus ? { status: v.hepatiteCStatus, dataColeta: v.hepatiteCData } : null,
      toxoplasmose: v.toxoplasmoseStatus ? { status: v.toxoplasmoseStatus, dataColeta: v.toxoplasmoseData } : null,
      usgObstetrica: v.usgData ? {
        data: v.usgData, igUsg: v.usgIgUsg, biometria: v.usgBiometria, placenta: v.usgPlacenta,
      } : null,
    };
  }

  salvar(): void {
    this.salvando.set(true);
    const payload = this._buildPayload();
    const obs = this.dadosSalvos()
      ? this.svc.atualizarExamesLab(this.idConsulta, payload)
      : this.svc.salvarExamesLab(this.idConsulta, payload);

    obs.subscribe({
      next: (res) => {
        this.dadosSalvos.set(res);
        this.salvando.set(false);
        this.salvo.emit(res);
        this.snack.open('Exames laboratoriais salvos.', 'OK', { duration: 3000 });
      },
      error: () => {
        this.salvando.set(false);
        this.snack.open('Erro ao salvar exames.', 'OK', { duration: 4000 });
      },
    });
  }
}
