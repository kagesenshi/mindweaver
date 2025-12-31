import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import '../providers/chat_provider.dart';
import '../providers/ai_agent_provider.dart';
import '../models/chat.dart';

class ChatPage extends ConsumerWidget {
  const ChatPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      body: Row(
        children: [
          const SizedBox(width: 300, child: _ChatSidebar()),
          const VerticalDivider(width: 1),
          Expanded(child: _ChatContent()),
        ],
      ),
    );
  }
}

class _ChatSidebar extends ConsumerWidget {
  const _ChatSidebar();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final chatsAsync = ref.watch(chatListProvider);
    final activeChat = ref.watch(activeChatProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Chats'),
        actions: [
          IconButton(
            onPressed: () => _showNewChatDialog(context, ref),
            icon: const Icon(Icons.add_comment),
          ),
        ],
      ),
      body: chatsAsync.when(
        data: (chats) => ListView.builder(
          itemCount: chats.length,
          itemBuilder: (context, index) {
            final chat = chats[index];
            return ListTile(
              selected: activeChat?.id == chat.id,
              leading: const FaIcon(FontAwesomeIcons.message, size: 18),
              title: Text(chat.title),
              subtitle: Text(chat.agent_id ?? 'No Agent'),
              onTap: () =>
                  ref.read(activeChatProvider.notifier).setActiveChat(chat),
              trailing: IconButton(
                icon: const Icon(Icons.delete, size: 16),
                onPressed: () async {
                  await ref
                      .read(chatListProvider.notifier)
                      .deleteChat(chat.id!);
                  ref.invalidate(chatListProvider);
                },
              ),
            );
          },
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Error: $err')),
      ),
    );
  }

  void _showNewChatDialog(BuildContext context, WidgetRef ref) {
    final titleController = TextEditingController();
    String? selectedAgentId;
    final agentsAsync = ref.read(aiAgentListProvider);

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Text('New Chat'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: titleController,
                decoration: const InputDecoration(labelText: 'Chat Title'),
              ),
              const SizedBox(height: 20),
              agentsAsync.when(
                data: (agents) => DropdownButtonFormField<String?>(
                  initialValue: selectedAgentId,
                  decoration: const InputDecoration(
                    labelText: 'AI Agent (Optional)',
                  ),
                  items: [
                    const DropdownMenuItem(value: null, child: Text('Default')),
                    ...agents.map(
                      (a) =>
                          DropdownMenuItem(value: a.uuid, child: Text(a.title)),
                    ),
                  ],
                  onChanged: (val) => setState(() => selectedAgentId = val),
                ),
                loading: () => const CircularProgressIndicator(),
                error: (err, _) => Text('Error: $err'),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () async {
                final chat = await ref
                    .read(chatListProvider.notifier)
                    .createChat(titleController.text, selectedAgentId);
                ref.invalidate(chatListProvider);
                ref.read(activeChatProvider.notifier).setActiveChat(chat);
                if (context.mounted) Navigator.pop(context);
              },
              child: const Text('Create'),
            ),
          ],
        ),
      ),
    );
  }
}

class _ChatContent extends ConsumerWidget {
  final TextEditingController _msgController = TextEditingController();

  _ChatContent();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final chat = ref.watch(activeChatProvider);

    if (chat == null) {
      return const Center(child: Text('Select or create a chat to begin.'));
    }

    return Column(
      children: [
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.all(20),
            itemCount: chat.messages.length,
            itemBuilder: (context, index) {
              final msg = chat.messages[index];
              final isUser = msg['role'] == 'user';
              return Align(
                alignment: isUser
                    ? Alignment.centerRight
                    : Alignment.centerLeft,
                child: Container(
                  margin: const EdgeInsets.symmetric(vertical: 5),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: isUser ? Colors.blue.shade100 : Colors.grey.shade200,
                    borderRadius: BorderRadius.circular(15),
                  ),
                  child: Text(msg['content'] ?? ''),
                ),
              );
            },
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(20),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _msgController,
                  decoration: const InputDecoration(
                    hintText: 'Type a message...',
                    border: OutlineInputBorder(),
                  ),
                  onSubmitted: (val) => _send(ref),
                ),
              ),
              const SizedBox(width: 10),
              IconButton(
                onPressed: () => _send(ref),
                icon: const Icon(Icons.send, color: Colors.blue),
              ),
            ],
          ),
        ),
      ],
    );
  }

  void _send(WidgetRef ref) {
    if (_msgController.text.trim().isEmpty) return;
    ref.read(activeChatProvider.notifier).sendMessage(_msgController.text);
    _msgController.clear();
  }
}
