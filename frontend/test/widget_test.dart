// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mindweaver_flutter/main.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Mindweaver smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: MindweaverApp()));

    // Verify that the app title is present.
    expect(find.text('Mindweaver'), findsOneWidget);

    // Verify that the Projects page is loaded by checking for the AppBar title.
    expect(find.text('Projects'), findsWidgets);
  });
}
