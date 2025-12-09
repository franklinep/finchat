import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { ArchivoProcesado, CamposClave } from '../types/receipts';
import { RouteProp, useRoute } from '@react-navigation/native';

type ReceiptDetailRoute = RouteProp<{ params: { receipt?: ArchivoProcesado } }, 'params'>;

const formatCurrency = (value?: number | null, symbol = 'S/') => {
  if (value === undefined || value === null || Number.isNaN(value)) return '-';
  return `${symbol} ${value.toFixed(2)}`;
};

export const ReceiptDetailScreen = () => {
  const route = useRoute<ReceiptDetailRoute>();
  const receipt = route.params?.receipt;
  const campos: CamposClave | undefined = receipt?.camposClave;

  if (!receipt) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={[typography.body, { color: colors.textSecondary }]}>
          No se pudo cargar el detalle del comprobante.
        </Text>
      </View>
    );
  }

  const porcentaje = receipt.clasificacion?.porcentajeDeduccion;
  const estadoSunat = receipt.validacionSunat?.estadoRuc || 'Pendiente';

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={[typography.h2, styles.title]}>Detalle del Gasto</Text>

      <View style={styles.summaryCard}>
        <Text style={[typography.bodySmall, styles.badge]}>
          {receipt.esDuplicado ? 'Posible duplicado' : 'Validado'}
        </Text>
        <Text style={[typography.h3, styles.summaryTitle]}>
          {receipt.clasificacion?.categoriaGasto || 'Clasificación pendiente'}
        </Text>
        <Text style={[typography.body, styles.summaryLine]}>
          Regla de deducción: {porcentaje ? `${porcentaje}%` : '—'}
        </Text>
        <Text style={[typography.body, styles.summaryLine]}>
          Validación SUNAT: {estadoSunat}
        </Text>
        <Text style={[typography.body, styles.summaryLine]}>
          Total: {formatCurrency(campos?.monto_total, campos?.moneda || 'S/')}
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={[typography.h3, styles.sectionTitle]}>Datos del Emisor</Text>
        <View style={styles.row}>
          <Text style={styles.label}>RUC</Text>
        <Text style={styles.value}>{campos?.ruc_emisor || 'No disponible'}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Serie - Número</Text>
          <Text style={styles.value}>{campos?.serie_numero || '-'}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Fecha emisión</Text>
          <Text style={styles.value}>{campos?.fecha_emision || '-'}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Tipo</Text>
          <Text style={styles.value}>{campos?.tipo_comprobante || '-'}</Text>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={[typography.h3, styles.sectionTitle]}>Montos</Text>
        <View style={styles.row}>
          <Text style={styles.label}>Monto total</Text>
          <Text style={styles.value}>{formatCurrency(campos?.monto_total, campos?.moneda || 'S/')}</Text>
        </View>
        {porcentaje !== undefined && (
          <View style={styles.row}>
            <Text style={styles.label}>Deducción aplicada</Text>
            <Text style={styles.value}>{`${porcentaje}%`}</Text>
          </View>
        )}
      </View>

      <View style={styles.section}>
        <Text style={[typography.h3, styles.sectionTitle]}>Validación SUNAT</Text>
        <View style={styles.row}>
          <Text style={styles.label}>Condición RUC</Text>
          <Text style={styles.value}>{receipt.validacionSunat?.condicionRuc || '-'}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Estado RUC</Text>
          <Text style={styles.value}>{receipt.validacionSunat?.estadoRuc || '-'}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>CIIU</Text>
          <Text style={styles.value}>{receipt.validacionSunat?.ciiuPrincipal || '-'}</Text>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: 20,
    gap: 16,
  },
  title: {
    color: colors.text,
  },
  summaryCard: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 6,
  },
  badge: {
    alignSelf: 'flex-start',
    backgroundColor: colors.secondary + '20',
    color: colors.secondary,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    overflow: 'hidden',
    fontWeight: '700',
  },
  summaryTitle: {
    color: colors.text,
  },
  summaryLine: {
    color: colors.textSecondary,
  },
  section: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: colors.border,
  },
  sectionTitle: {
    color: colors.text,
    marginBottom: 12,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  label: {
    color: colors.textSecondary,
  },
  value: {
    color: colors.text,
    fontWeight: '600',
    textAlign: 'right',
    marginLeft: 12,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
  },
});
