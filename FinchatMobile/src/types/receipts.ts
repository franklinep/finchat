export interface CamposClave {
  ruc_emisor?: string;
  serie_numero?: string;
  fecha_emision?: string;
  moneda?: string;
  monto_total?: number;
  nombre_cliente?: string;
  doc_cliente?: string;
  tipo_comprobante?: string;
}

export interface ValidacionSunatOut {
  ruc: string;
  estadoRuc?: string | null;
  condicionRuc?: string | null;
  ciiuPrincipal?: string | null;
  pasaReglasBasicas?: boolean | null;
  motivoNoDeducible?: string | null;
}

export interface ClasificacionOut {
  categoriaGasto: string;
  porcentajeDeduccion: number;
  versionRegla: string;
}

export interface ArchivoProcesado {
  nombreArchivo: string;
  hashArchivo?: string | null;
  esDuplicado: boolean;
  idComprobante?: number | null;
  camposClave?: CamposClave;
  validacionSunat?: ValidacionSunatOut;
  clasificacion?: ClasificacionOut;
}

export interface SubirComprobantesResponse {
  usuarioId: number;
  totalArchivos: number;
  procesados: ArchivoProcesado[];
}

export interface ConsultaResponse {
  tipo: string;
  respuesta: string;
  datos?: Array<Record<string, any>> | null;
  totales?: Record<string, any> | null;
}
