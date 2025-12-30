import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/chat.dart';
import 'api_providers.dart';

class ChatListNotifier extends StateNotifier<AsyncValue<List<Chat>>> {
  final Ref ref;

  ChatListNotifier(this.ref) : super(const AsyncValue.loading()) {
    loadChats();
  }

  Future<void> loadChats() async {
    state = const AsyncValue.loading();
    try {
      final client = ref.read(apiClientProvider);
      final response = await client.listAll(
        '/api/v1/chats',
        (json) => Chat.fromJson(json as Map<String, dynamic>),
      );
      state = AsyncValue.data(response);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<Chat> createChat(String title, String? agentId) async {
    try {
      final client = ref.read(apiClientProvider);
      final response = await client.post('/api/v1/chats', {
        'name': title.toLowerCase().replaceAll(' ', '-'),
        'title': title,
        'agent_id': agentId,
        'messages': [],
      }, (json) => Chat.fromJson(json as Map<String, dynamic>));
      await loadChats();
      return response.record!;
    } catch (e) {
      rethrow;
    }
  }

  Future<void> deleteChat(int id) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.delete('/api/v1/chats/$id');
      await loadChats();
    } catch (e) {
      rethrow;
    }
  }
}

final chatListProvider =
    StateNotifierProvider<ChatListNotifier, AsyncValue<List<Chat>>>((ref) {
      return ChatListNotifier(ref);
    });

class ActiveChatNotifier extends StateNotifier<Chat?> {
  final Ref ref;

  ActiveChatNotifier(this.ref) : super(null);

  void setActiveChat(Chat chat) {
    state = chat;
  }

  Future<void> sendMessage(String text) async {
    if (state == null) return;

    final newMessage = {'role': 'user', 'content': text};
    final updatedMessages = [...state!.messages, newMessage];

    // Optimistic update
    state = Chat(
      id: state!.id,
      uuid: state!.uuid,
      name: state!.name,
      title: state!.title,
      project_id: state!.project_id,
      agent_id: state!.agent_id,
      messages: updatedMessages,
    );

    try {
      final client = ref.read(apiClientProvider);
      final response = await client.put(
        '/api/v1/chats/${state!.id}',
        {'messages': updatedMessages},
        (json) => Chat.fromJson(json as Map<String, dynamic>),
      );
      state = response.record;
    } catch (e) {
      // Handle error (maybe rollback)
      rethrow;
    }
  }
}

final activeChatProvider = StateNotifierProvider<ActiveChatNotifier, Chat?>((
  ref,
) {
  return ActiveChatNotifier(ref);
});
