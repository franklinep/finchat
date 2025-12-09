import React, { useState } from 'react';
import { View, StyleSheet, FlatList, TextInput, KeyboardAvoidingView, Platform, Text } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { IconButton } from 'react-native-paper';
import * as DocumentPicker from 'expo-document-picker';
import { useChat } from '../context/ChatContext';
import { MessageBubble } from '../components/MessageBubble';
import { colors } from '../theme/colors';
import { useNavigation } from '@react-navigation/native';
import { receiptService, UploadableFile, formatProcessedReceipt } from '../services/receiptService';
import { Message } from '../types/chat';

export const ChatScreen = () => {
  const { messages, sendMessage, isLoading, addMessage } = useChat();
  const [inputText, setInputText] = useState('');
  const navigation = useNavigation<any>();
  const [isUploading, setIsUploading] = useState(false);
  const [isConsulting, setIsConsulting] = useState(false);

  const handleSend = async () => {
    if (inputText.trim()) {
      const text = inputText;
      setInputText('');
      await sendMessage(text);
    }
  };

  const handleUpload = async () => {
    const result = await DocumentPicker.getDocumentAsync({
      multiple: false,
      copyToCacheDirectory: true,
      type: ['application/pdf', 'image/jpeg', 'image/png', 'image/*'],
    });

    if (result.canceled) return;

    const files: UploadableFile[] = result.assets.map((asset, idx) => ({
      uri: asset.uri,
      name: asset.name || `comprobante-${idx + 1}.pdf`,
      type: asset.mimeType || 'application/pdf',
    }));

    setIsUploading(true);
    try {
      const response = await receiptService.uploadReceipts(files);
      const processed = response.procesados?.[0];

      if (processed) {
        addMessage({
          id: Date.now().toString(),
          text: `Comprobante procesado: ${formatProcessedReceipt(processed)}`,
          sender: 'system',
          timestamp: new Date(),
        });
        navigation.navigate('ReceiptDetail', { receipt: processed });
      }
    } catch (error) {
      console.error('Upload from chat error', error);
      addMessage({
        id: Date.now().toString(),
        text: 'No se pudo subir el comprobante. Intenta nuevamente.',
        sender: 'system',
        timestamp: new Date(),
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleSettings = () => {
    navigation.navigate('Settings');
  };

  const handleConsult = async () => {
    if (!inputText.trim()) return;
    const text = inputText.trim();
    setInputText('');

    const userMessage: Message = {
      id: Date.now().toString(),
      text,
      sender: 'user',
      timestamp: new Date(),
    };
    addMessage(userMessage);
    setIsConsulting(true);

    try {
      const response = await receiptService.consultReceipts(text);
      const summary = response.respuesta;
      addMessage({
        id: `${Date.now()}-res`,
        text: summary,
        sender: 'system',
        timestamp: new Date(),
      });
    } catch (error) {
      console.error('Consulta comprobantes error', error);
      addMessage({
        id: `${Date.now()}-error`,
        text: 'No pudimos consultar tus comprobantes ahora mismo.',
        sender: 'system',
        timestamp: new Date(),
      });
    } finally {
      setIsConsulting(false);
    }
  };

  const isBusy = isLoading || isUploading || isConsulting;

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Finchat</Text>
        <IconButton icon="cog" iconColor={colors.primary} onPress={handleSettings} />
      </View>

      <FlatList
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <MessageBubble message={item} />}
        contentContainerStyle={styles.listContent}
        inverted={false} // Normal order for now, or true if we want bottom-up
      />

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      >
        <View style={styles.inputContainer}>
          <IconButton icon="paperclip" iconColor={colors.textSecondary} onPress={handleUpload} disabled={isBusy} />
          <TextInput
            style={styles.input}
            placeholder="Escribe un mensaje..."
            value={inputText}
            onChangeText={setInputText}
            placeholderTextColor={colors.textSecondary}
          />
          <IconButton
            icon="magnify"
            iconColor={colors.textSecondary}
            onPress={handleConsult}
            disabled={!inputText.trim() || isBusy}
          />
          <IconButton
            icon="send"
            iconColor={colors.primary}
            onPress={handleSend}
            disabled={!inputText.trim() || isBusy}
          />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.primary,
  },
  listContent: {
    padding: 16,
    paddingBottom: 80,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 8,
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  input: {
    flex: 1,
    backgroundColor: colors.background,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginHorizontal: 8,
    color: colors.text,
    maxHeight: 100,
  },
});
