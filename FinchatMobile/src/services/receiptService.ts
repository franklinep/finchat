import { apiClient } from './apiClient';
import { ArchivoProcesado, SubirComprobantesResponse, ConsultaResponse } from '../types/receipts';

export interface UploadableFile {
  uri: string;
  name: string;
  type?: string;
}

export const receiptService = {
  async uploadReceipts(files: UploadableFile[]): Promise<SubirComprobantesResponse> {
    const formData = new FormData();

    files.forEach((file) => {
      formData.append('archivos', {
        uri: file.uri,
        name: file.name,
        type: file.type || 'application/pdf',
      } as any);
    });

    const response = await apiClient.post<SubirComprobantesResponse>(
      '/comprobantes/subir',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );

    return response.data;
  },

  async consultReceipts(message: string): Promise<ConsultaResponse> {
    const response = await apiClient.post<ConsultaResponse>('/comprobantes/consultar', {
      mensaje: message,
    });

    return response.data;
  },
};

export const formatProcessedReceipt = (item: ArchivoProcesado) => {
  const monto = item.camposClave?.monto_total;
  const moneda = item.camposClave?.moneda || 'S/';
  const deduccion = item.clasificacion?.porcentajeDeduccion;
  const duplicado = item.esDuplicado;

  const parts = [
    item.nombreArchivo,
    monto ? `${moneda} ${monto.toFixed(2)}` : undefined,
    deduccion !== undefined ? `Deducción ${deduccion}%` : undefined,
    duplicado ? 'Posible duplicado' : undefined,
  ].filter(Boolean);

  return parts.join(' | ');
};
