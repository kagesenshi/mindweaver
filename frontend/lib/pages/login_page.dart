import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'dart:html' as html; // For web redirection
import '../providers/auth_provider.dart';

class LoginPage extends ConsumerStatefulWidget {
  final String? code;
  final String? error;

  const LoginPage({super.key, this.code, this.error});

  @override
  ConsumerState<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends ConsumerState<LoginPage> {
  bool _isLoading = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    if (widget.code != null) {
      _handleCallback(widget.code!);
    }
    if (widget.error != null) {
      setState(() {
        _errorMessage = widget.error;
      });
    }
  }

  Future<void> _handleCallback(String code) async {
    setState(() {
      _isLoading = true;
    });

    try {
      // The redirect URL must match exactly what was sent during login
      // We need to construct it same way.
      // Assuming the app is handling this route, the URL is window.location.href (without query)
      // or we can reconstruct it.
      // For simplicity, we assume http://localhost:PORT/login (or whatever the route is)
      // But actually, we need to send the EXACT url that was used as redirect_uri.
      // If we use `html.window.location.href` it might contain the code.
      // We should pass the BASE redirect url (e.g. http://localhost:8080/login)

      final currentUrl = Uri.base;
      // Remove query params to get the base redirect URL
      final redirectUrl = currentUrl.replace(queryParameters: {}).toString();

      await ref.read(authProvider.notifier).handleCallback(code, redirectUrl);

      if (mounted) {
        context.go('/'); // Redirect to home on success
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = 'Login failed: $e';
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _login() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final currentUrl = Uri.base;
      final redirectUrl = currentUrl.replace(queryParameters: {}).toString();

      final loginUrl = await ref
          .read(authProvider.notifier)
          .getLoginUrl(redirectUrl);

      // Redirect browser
      html.window.location.href = loginUrl;
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = 'Could not initiate login: $e';
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Container(
          constraints: const BoxConstraints(maxWidth: 400),
          padding: const EdgeInsets.all(30),
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.surface,
            borderRadius: BorderRadius.circular(20),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.1),
                blurRadius: 20,
                offset: const Offset(0, 5),
              ),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Mindweaver',
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: Theme.of(context).colorScheme.primary,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                'Welcome back',
                style: Theme.of(context).textTheme.bodyLarge,
              ),
              const SizedBox(height: 40),
              if (_errorMessage != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 20),
                  child: Text(
                    _errorMessage!,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
              if (_isLoading)
                const CircularProgressIndicator()
              else
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: FilledButton(
                    onPressed: _login,
                    child: const Text('Login with OIDC'),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
