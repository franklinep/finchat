export interface Emisor {
  ruc: string;
  razonSocial: string;
  nombreComercial?: string;
  estadoRuc: string;
  condicionRuc: string;
}

export interface DetalleItem {
  descripcion: string;
  cantidad: number;
  precioUnitario: number;
  montoItem: number;
}

export interface Comprobante {
  id: string;
  emisor: Emisor;
  serie: string;
  numero: string;
  fechaEmision: string;
  montoTotal: number;
  moneda: string;
  origen: 'fisico' | 'electronico';
  categoriaGasto: string;
  porcentajeDeduccion: number;
  montoDeducible: number;
  esDeducible: boolean;
  esDuplicado: boolean;
  items: DetalleItem[];
  validacion: {
    coincideNombre: boolean;
    pasaReglas: boolean;
  };
}
