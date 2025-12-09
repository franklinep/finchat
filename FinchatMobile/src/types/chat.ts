export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'system';
  timestamp: Date;
  relatedReceipts?: ReceiptSummary[]; // Si el mensaje trae resumen de boletas
}

export interface ReceiptSummary {
  count: number;
  totalAmount: number;
  deductibleAmount: number;
  receiptIds: string[];
}
