import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/auth_provider.dart';

class CallbackPage extends ConsumerStatefulWidget {
  final String? code;
  final String? state;
  final String? error;

  const CallbackPage({super.key, this.code, this.state, this.error});

  @override
  ConsumerState<CallbackPage> createState() => _CallbackPageState();
}

class _CallbackPageState extends ConsumerState<CallbackPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _handleCallback();
    });
  }

  Future<void> _handleCallback() async {
    if (widget.error != null) {
      if (mounted) {
        context.go('/login?error=${Uri.encodeComponent(widget.error!)}');
      }
      return;
    }

    if (widget.code == null) {
      if (mounted) {
        context.go('/login?error=Missing+code');
      }
      return;
    }

    try {
      final currentUrl = Uri.base;
      // The redirect URL must match exactly what was sent during login
      // Which will be the current URL without query parameters.
      final redirectUrl = currentUrl.replace(queryParameters: {}).toString();

      await ref
          .read(authProvider.notifier)
          .handleCallback(widget.code!, redirectUrl);

      if (mounted) {
        context.go('/'); // Success
      }
    } catch (e) {
      if (mounted) {
        context.go('/login?error=${Uri.encodeComponent(e.toString())}');
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Processing login...'),
          ],
        ),
      ),
    );
  }
}
