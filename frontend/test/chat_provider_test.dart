import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mindweaver_flutter/models/chat.dart';
import 'package:mindweaver_flutter/providers/api_providers.dart';
import 'package:mindweaver_flutter/providers/chat_provider.dart';
import 'mocks/api_client_mock.dart';

void main() {
  late MockApiClient mockClient;
  late ProviderContainer container;

  setUp(() {
    mockClient = MockApiClient();
    container = ProviderContainer(
      overrides: [apiClientProvider.overrideWithValue(mockClient)],
    );
  });

  tearDown(() {
    container.dispose();
  });

  group('ChatListNotifier', () {
    test('loadChats fetches data correctly', () async {
      final notifier = container.read(chatListProvider.notifier);
      final chatData = [
        {
          'id': 1,
          'name': 'chat-1',
          'title': 'Chat 1',
          'messages': [],
          'project_id': 123,
        },
      ];
      mockClient.setMockResponse(chatData);

      await notifier.loadChats();

      expect(notifier.state.hasValue, true);
      expect(notifier.state.value!.length, 1);
      expect(notifier.state.value!.first.title, 'Chat 1');
      expect(mockClient.lastMethod, 'GET_LIST');
      expect(mockClient.lastEndpoint, '/api/v1/chats');
    });

    test('createChat sends correct parameters', () async {
      final notifier = container.read(chatListProvider.notifier);

      final createdChat = Chat(
        id: 1,
        name: 'new-chat',
        title: 'New Chat',
        messages: [],
        project_id: 55,
        agent_id: 'agent_id',
      );
      mockClient.setMockResponse(createdChat.toJson());

      final result = await notifier.createChat(
        'New Chat',
        'agent_id',
        project_id: 55,
      );

      expect(mockClient.lastMethod, 'POST');
      expect(mockClient.lastEndpoint, '/api/v1/chats');
      expect(mockClient.lastBody, isA<Map>());
      final body = mockClient.lastBody as Map<String, dynamic>;
      expect(body['title'], 'New Chat');
      expect(
        body['name'],
        'new-chat',
      ); // validation logic checks regex replacement
      expect(body['agent_id'], 'agent_id');
      expect(body['project_id'], 55);
      expect(result.id, 1);
    });

    test('deleteChat calls correct endpoint', () async {
      final notifier = container.read(chatListProvider.notifier);

      await notifier.deleteChat(33);

      expect(mockClient.lastMethod, 'DELETE');
      expect(mockClient.lastEndpoint, '/api/v1/chats/33');
    });
  });

  group('ActiveChatNotifier', () {
    test('sendMessage updates state and calls API', () async {
      final notifier = container.read(activeChatProvider.notifier);
      final initialChat = Chat(
        id: 100,
        name: 'test-chat',
        title: 'Test Chat',
        messages: [
          {'role': 'system', 'content': 'Hi'},
        ],
      );

      notifier.setActiveChat(initialChat);

      final updatedChat = Chat(
        id: 100,
        name: 'test-chat',
        title: 'Test Chat',
        messages: [
          {'role': 'system', 'content': 'Hi'},
          {'role': 'user', 'content': 'Hello world'},
        ],
      );

      mockClient.setMockResponse(updatedChat.toJson());

      await notifier.sendMessage('Hello world');

      expect(mockClient.lastMethod, 'PUT');
      expect(mockClient.lastEndpoint, '/api/v1/chats/100');
      final body = mockClient.lastBody as Map<String, dynamic>;
      expect(body['messages'].length, 2);
      expect(body['messages'].last['content'], 'Hello world');

      expect(notifier.state!.messages.length, 2);
    });
  });
}
