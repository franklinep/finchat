import React, { useMemo, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, FlatList } from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import { useNavigation } from '@react-navigation/native';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { receiptService, UploadableFile } from '../services/receiptService';
import { ArchivoProcesado } from '../types/receipts';
import { LoadingOverlay } from '../components/LoadingOverlay';

type StepStatus = 'pending' | 'current' | 'done' | 'error';

const baseSteps = [
  'Subiendo archivo...',
  'Extrayendo texto (OCR)...',
  'Consultando SUNAT y reglas...',
  'Analizando...',
];

export const UploadReceiptScreen = () => {
  const navigation = useNavigation<any>();
  const [selectedFiles, setSelectedFiles] = useState<UploadableFile[]>([]);
  const [steps, setSteps] = useState<StepStatus[]>(Array(baseSteps.length).fill('pending'));
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const hasSelection = selectedFiles.length > 0;

  const statusColor = (status: StepStatus) => {
    switch (status) {
      case 'done':
        return colors.secondary;
      case 'current':
        return colors.primary;
      case 'error':
        return colors.error;
      default:
        return colors.textSecondary;
    }
  };

  const pickFiles = async () => {
    const result = await DocumentPicker.getDocumentAsync({
      multiple: true,
      copyToCacheDirectory: true,
      type: ['application/pdf', 'image/jpeg', 'image/png', 'image/*'],
    });

    if (!result.canceled) {
      const files: UploadableFile[] = result.assets.map((asset, idx) => ({
        uri: asset.uri,
        name: asset.name || `comprobante-${idx + 1}.pdf`,
        type: asset.mimeType || 'application/pdf',
      }));
      setSelectedFiles(files);
    }
  };

  const resetSteps = () => setSteps(baseSteps.map((_, idx) => (idx === 0 ? 'current' : 'pending')));

  const markStepsDone = () => setSteps(baseSteps.map(() => 'done'));

  const handleUpload = async () => {
    if (!hasSelection) {
      setError('Selecciona al menos un archivo para continuar.');
      return;
    }

    setError(null);
    setIsProcessing(true);
    resetSteps();

    try {
      const response = await receiptService.uploadReceipts(selectedFiles);
      markStepsDone();
      const first: ArchivoProcesado | undefined = response.procesados?.[0];
      setSelectedFiles([]);

      if (first) {
        navigation.navigate('ReceiptDetail', { receipt: first });
      }
    } catch (err) {
      console.error('Upload error', err);
      setSteps(baseSteps.map((_, idx) => (idx === 0 ? 'error' : 'pending')));
      setError('No se pudo subir el comprobante. Intenta nuevamente.');
    } finally {
      setIsProcessing(false);
    }
  };

  const renderStep = ({ item, index }: { item: string; index: number }) => {
    const status = steps[index];
    return (
      <View style={styles.stepRow}>
        <View style={[styles.stepDot, { backgroundColor: statusColor(status) }]} />
        <Text style={[typography.bodySmall, { color: statusColor(status) }]}>{item}</Text>
      </View>
    );
  };

  const selectedLabel = useMemo(() => {
    if (!selectedFiles.length) return 'Ningun archivo seleccionado';
    if (selectedFiles.length === 1) return selectedFiles[0].name;
    return `${selectedFiles.length} archivos seleccionados`;
  }, [selectedFiles]);

  return (
    <View style={styles.container}>
      <Text style={[typography.h2, styles.title]}>Subir Comprobante</Text>
      <Text style={[typography.body, styles.subtitle]}>
        Adjunta tu comprobante en PDF o imagen. Lo procesaremos y validaremos con SUNAT.
      </Text>

      <TouchableOpacity style={styles.selector} onPress={pickFiles}>
        <Text style={[typography.body, styles.selectorText]}>Elegir archivo</Text>
        <Text style={[typography.caption, styles.selectorHint]}>{selectedLabel}</Text>
      </TouchableOpacity>

      <View style={styles.stepsCard}>
        <Text style={[typography.h3, styles.stepsTitle]}>Proceso</Text>
        <FlatList
          data={baseSteps}
          renderItem={renderStep}
          keyExtractor={(item, idx) => `${item}-${idx}`}
          ItemSeparatorComponent={() => <View style={styles.separator} />}
        />
      </View>

      {error && <Text style={[typography.bodySmall, styles.error]}>{error}</Text>}

      <TouchableOpacity
        style={[styles.uploadButton, !hasSelection && styles.buttonDisabled]}
        onPress={handleUpload}
        disabled={!hasSelection || isProcessing}
      >
        <Text style={styles.uploadButtonText}>{isProcessing ? 'Procesando...' : 'Subir y validar'}</Text>
      </TouchableOpacity>

      <LoadingOverlay visible={isProcessing} message="Procesando comprobante..." />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: colors.background,
    gap: 16,
  },
  title: {
    color: colors.text,
  },
  subtitle: {
    color: colors.textSecondary,
  },
  selector: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: colors.border,
  },
  selectorText: {
    color: colors.primary,
    fontWeight: '700',
  },
  selectorHint: {
    marginTop: 8,
    color: colors.textSecondary,
  },
  stepsCard: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: colors.border,
  },
  stepsTitle: {
    color: colors.text,
    marginBottom: 12,
  },
  stepRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  stepDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  separator: {
    height: 10,
  },
  uploadButton: {
    backgroundColor: colors.primary,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  uploadButtonText: {
    color: colors.surface,
    fontWeight: '700',
    fontSize: 16,
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  error: {
    color: colors.error,
  },
});
