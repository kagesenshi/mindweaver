import 'package:flutter/material.dart';

class LargeDialog extends StatelessWidget {
  final String title;
  final Widget child;
  final List<Widget> actions;

  const LargeDialog({
    super.key,
    required this.title,
    required this.child,
    required this.actions,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    // Custom dark colors similar to the screenshot
    const darkBg = Color(0xFF0F111A);
    const darkSurface = Color(0xFF161922);
    const accentColor = Color(0xFF646CFF);

    return Dialog(
      backgroundColor: isDark ? darkBg : theme.dialogBackgroundColor,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Container(
        width: MediaQuery.of(context).size.width * 0.7,
        constraints: const BoxConstraints(maxWidth: 900),
        decoration: BoxDecoration(
          color: isDark ? darkSurface : theme.dialogBackgroundColor,
          borderRadius: BorderRadius.circular(16),
        ),
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  title,
                  style: theme.textTheme.headlineMedium?.copyWith(
                    color: isDark ? Colors.white : null,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                IconButton(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.close),
                  color: isDark ? Colors.white60 : null,
                ),
              ],
            ),
            const SizedBox(height: 32),
            Flexible(
              child: SingleChildScrollView(
                child: Theme(
                  data: theme.copyWith(
                    inputDecorationTheme: InputDecorationTheme(
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                        borderSide: BorderSide(
                          color: isDark ? Colors.white24 : Colors.grey.shade300,
                        ),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                        borderSide: const BorderSide(
                          color: accentColor,
                          width: 2,
                        ),
                      ),
                      labelStyle: TextStyle(
                        color: isDark ? Colors.white70 : Colors.grey.shade700,
                      ),
                      hintStyle: TextStyle(
                        color: isDark ? Colors.white30 : Colors.grey.shade400,
                      ),
                    ),
                  ),
                  child: child,
                ),
              ),
            ),
            const SizedBox(height: 32),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: actions.map((a) {
                return Padding(
                  padding: const EdgeInsets.only(left: 12),
                  child: a,
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }
}
