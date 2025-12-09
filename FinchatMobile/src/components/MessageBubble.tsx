import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { Message } from '../types/chat';

interface Props {
  message: Message;
}

export const MessageBubble: React.FC<Props> = ({ message }) => {
  const isUser = message.sender === 'user';

  return (
    <View
      style={[
        styles.container,
        isUser ? styles.userContainer : styles.systemContainer,
      ]}
    >
      <View
        style={[
          styles.bubble,
          isUser ? styles.userBubble : styles.systemBubble,
        ]}
      >
        <Text
          style={[
            typography.body,
            isUser ? styles.userText : styles.systemText,
          ]}
        >
          {message.text}
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 4,
    flexDirection: 'row',
    width: '100%',
  },
  userContainer: {
    justifyContent: 'flex-end',
  },
  systemContainer: {
    justifyContent: 'flex-start',
  },
  bubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 16,
  },
  userBubble: {
    backgroundColor: colors.userBubble,
    borderBottomRightRadius: 4,
  },
  systemBubble: {
    backgroundColor: colors.systemBubble,
    borderBottomLeftRadius: 4,
  },
  userText: {
    color: colors.userText,
  },
  systemText: {
    color: colors.systemText,
  },
});
