import 'package:flutter/material.dart';

class SearchableMultiSelect<T> extends StatefulWidget {
  final String label;
  final List<T> items;
  final List<T> selectedItems;
  final String Function(T) itemLabel;
  final dynamic Function(T) itemId;
  final Function(List<T>) onChanged;
  final bool isImmutable;

  const SearchableMultiSelect({
    super.key,
    required this.label,
    required this.items,
    required this.selectedItems,
    required this.itemLabel,
    required this.itemId,
    required this.onChanged,
    this.isImmutable = false,
  });

  @override
  State<SearchableMultiSelect<T>> createState() =>
      _SearchableMultiSelectState<T>();
}

class _SearchableMultiSelectState<T> extends State<SearchableMultiSelect<T>> {
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(widget.label, style: theme.textTheme.bodySmall),
        const SizedBox(height: 8),
        InkWell(
          onTap: widget.isImmutable ? null : _showSearchDialog,
          child: InputDecorator(
            decoration: InputDecoration(
              enabled: !widget.isImmutable,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
              ),
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 12,
                vertical: 8,
              ),
            ),
            child: Row(
              children: [
                Expanded(
                  child: widget.selectedItems.isEmpty
                      ? Text(
                          'Select ${widget.label}...',
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: theme.hintColor,
                          ),
                        )
                      : Wrap(
                          spacing: 4,
                          runSpacing: 4,
                          children: widget.selectedItems.map((item) {
                            return Chip(
                              label: Text(
                                widget.itemLabel(item),
                                style: const TextStyle(fontSize: 12),
                              ),
                              padding: EdgeInsets.zero,
                              materialTapTargetSize:
                                  MaterialTapTargetSize.shrinkWrap,
                              onDeleted: widget.isImmutable
                                  ? null
                                  : () {
                                      final newList = List<T>.from(
                                        widget.selectedItems,
                                      );
                                      newList.removeWhere(
                                        (i) =>
                                            widget.itemId(i) ==
                                            widget.itemId(item),
                                      );
                                      widget.onChanged(newList);
                                    },
                            );
                          }).toList(),
                        ),
                ),
                Icon(Icons.arrow_drop_down, color: theme.hintColor),
              ],
            ),
          ),
        ),
      ],
    );
  }

  void _showSearchDialog() async {
    final List<T>? result = await showDialog<List<T>>(
      context: context,
      builder: (context) => _SearchDialog<T>(
        title: widget.label,
        items: widget.items,
        initialSelectedItems: widget.selectedItems,
        itemLabel: widget.itemLabel,
        itemId: widget.itemId,
      ),
    );

    if (result != null) {
      widget.onChanged(result);
    }
  }
}

class _SearchDialog<T> extends StatefulWidget {
  final String title;
  final List<T> items;
  final List<T> initialSelectedItems;
  final String Function(T) itemLabel;
  final dynamic Function(T) itemId;

  const _SearchDialog({
    required this.title,
    required this.items,
    required this.initialSelectedItems,
    required this.itemLabel,
    required this.itemId,
  });

  @override
  State<_SearchDialog<T>> createState() => _SearchDialogState<T>();
}

class _SearchDialogState<T> extends State<_SearchDialog<T>> {
  late List<T> _selectedItems;
  late TextEditingController _searchController;
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _selectedItems = List<T>.from(widget.initialSelectedItems);
    _searchController = TextEditingController();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  List<T> get _filteredItems {
    if (_searchQuery.isEmpty) return widget.items;
    return widget.items.where((item) {
      return widget
          .itemLabel(item)
          .toLowerCase()
          .contains(_searchQuery.toLowerCase());
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Container(
        width: 400,
        height: 500,
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Select ${widget.title}',
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                IconButton(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.close),
                ),
              ],
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Search...',
                prefixIcon: const Icon(Icons.search),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              onChanged: (val) => setState(() => _searchQuery = val),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                TextButton(
                  onPressed: () {
                    setState(() {
                      _selectedItems = List<T>.from(widget.items);
                    });
                  },
                  child: const Text('Select All'),
                ),
                TextButton(
                  onPressed: () {
                    setState(() {
                      _selectedItems = [];
                    });
                  },
                  child: const Text('Clear All'),
                ),
              ],
            ),
            const Divider(),
            Expanded(
              child: ListView.builder(
                itemCount: _filteredItems.length,
                itemBuilder: (context, index) {
                  final item = _filteredItems[index];
                  final isSelected = _selectedItems.any(
                    (i) => widget.itemId(i) == widget.itemId(item),
                  );

                  return CheckboxListTile(
                    title: Text(widget.itemLabel(item)),
                    value: isSelected,
                    onChanged: (val) {
                      setState(() {
                        if (val == true) {
                          _selectedItems.add(item);
                        } else {
                          _selectedItems.removeWhere(
                            (i) => widget.itemId(i) == widget.itemId(item),
                          );
                        }
                      });
                    },
                    controlAffinity: ListTileControlAffinity.leading,
                    contentPadding: EdgeInsets.zero,
                  );
                },
              ),
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Cancel'),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: () => Navigator.pop(context, _selectedItems),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: theme.colorScheme.primary,
                    foregroundColor: theme.colorScheme.onPrimary,
                  ),
                  child: const Text('Confirm'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
