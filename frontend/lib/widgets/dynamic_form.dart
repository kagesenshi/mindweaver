import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/form_schema.dart';
import '../providers/api_providers.dart';

class DynamicForm extends ConsumerStatefulWidget {
  final FormSchema schema;
  final Map<String, dynamic>? initialValues;
  final Function(Map<String, dynamic>) onSaved;
  final bool isEdit;

  const DynamicForm({
    required GlobalKey<DynamicFormState> super.key,
    required this.schema,
    this.initialValues,
    required this.onSaved,
    this.isEdit = false,
  });

  @override
  ConsumerState<DynamicForm> createState() => DynamicFormState();
}

class DynamicFormState extends ConsumerState<DynamicForm> {
  final _formKey = GlobalKey<FormState>();
  final Map<String, dynamic> _formData = {};
  final Map<String, List<Map<String, dynamic>>> _relationshipOptions = {};

  @override
  void initState() {
    super.initState();
    _populateDefaults();
    if (widget.initialValues != null) {
      _formData.addAll(widget.initialValues!);
    }
    _fetchRelationshipOptions();
  }

  void _populateDefaults() {
    final properties =
        widget.schema.jsonschema['properties'] as Map<String, dynamic>? ?? {};
    for (var entry in properties.entries) {
      final fieldName = entry.key;
      final fieldSchema = entry.value as Map<String, dynamic>;

      // Check for default in jsonschema
      if (fieldSchema.containsKey('default')) {
        _formData[fieldName] = fieldSchema['default'];
      }

      // Override with widget metadata default if present
      final metadata = widget.schema.widgets[fieldName];
      if (metadata != null && metadata.defaultValue != null) {
        _formData[fieldName] = metadata.defaultValue;
      }
    }
  }

  Future<void> _fetchRelationshipOptions() async {
    final client = ref.read(apiClientProvider);
    for (var entry in widget.schema.widgets.entries) {
      final fieldName = entry.key;
      final metadata = entry.value;
      if (metadata.type == 'relationship' && metadata.endpoint != null) {
        try {
          final options = await client.listAll(
            metadata.endpoint!,
            (json) => json as Map<String, dynamic>,
          );
          if (mounted) {
            setState(() {
              _relationshipOptions[fieldName] = options;
            });
          }
        } catch (e) {
          debugPrint('Error fetching relationship options for $fieldName: $e');
        }
      }
    }
  }

  void submit() {
    if (_formKey.currentState!.validate()) {
      _formKey.currentState!.save();
      widget.onSaved(_formData);
    }
  }

  @override
  Widget build(BuildContext context) {
    final properties =
        widget.schema.jsonschema['properties'] as Map<String, dynamic>? ?? {};
    final requiredFields =
        (widget.schema.jsonschema['required'] as List<dynamic>?)
            ?.cast<String>() ??
        [];

    final fields = properties.entries
        .where((e) => !widget.schema.internal_fields.contains(e.key))
        .map((e) {
          final fieldName = e.key;
          final fieldSchema = e.value as Map<String, dynamic>;
          final metadata = widget.schema.widgets[fieldName];
          final isImmutable =
              widget.isEdit &&
              widget.schema.immutable_fields.contains(fieldName);
          final isRequired = requiredFields.contains(fieldName);

          return Padding(
            padding: const EdgeInsets.only(bottom: 16.0),
            child: _buildField(
              fieldName,
              fieldSchema,
              metadata,
              isImmutable,
              isRequired,
            ),
          );
        })
        .toList();

    final List<Widget> rows = [];
    for (var i = 0; i < fields.length; i += 2) {
      if (i + 1 < fields.length) {
        rows.add(
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(child: fields[i]),
              const SizedBox(width: 16),
              Expanded(child: fields[i + 1]),
            ],
          ),
        );
      } else {
        rows.add(
          Row(
            children: [
              Expanded(child: fields[i]),
              const SizedBox(width: 16),
              const Expanded(child: SizedBox()),
            ],
          ),
        );
      }
    }

    return Form(
      key: _formKey,
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: rows,
        ),
      ),
    );
  }

  Widget _buildField(
    String name,
    Map<String, dynamic> schema,
    WidgetMetadata? metadata,
    bool isImmutable,
    bool isRequired,
  ) {
    final label = schema['title'] ?? name;
    final type = schema['type'];

    if (metadata != null) {
      if (metadata.type == 'select' && metadata.options != null) {
        return _buildSelectField(
          name,
          label,
          metadata.options!,
          isImmutable,
          isRequired,
        );
      } else if (metadata.type == 'relationship') {
        return _buildRelationshipField(
          name,
          label,
          metadata,
          isImmutable,
          isRequired,
        );
      } else if (metadata.type == 'range') {
        return _buildRangeField(name, label, metadata, isImmutable, isRequired);
      }
    }

    if (type == 'boolean') {
      return SwitchListTile(
        title: Text(label),
        value: _formData[name] ?? false,
        onChanged: isImmutable
            ? null
            : (val) => setState(() => _formData[name] = val),
      );
    }

    if (type == 'number' || type == 'integer') {
      return TextFormField(
        initialValue: _formData[name]?.toString(),
        decoration: InputDecoration(labelText: label, enabled: !isImmutable),
        keyboardType: TextInputType.number,
        onSaved: (val) => _formData[name] = type == 'integer'
            ? int.tryParse(val ?? '')
            : double.tryParse(val ?? ''),
        validator: isRequired
            ? (val) => (val == null || val.isEmpty) ? 'Required' : null
            : null,
      );
    }

    // Default to text field
    return TextFormField(
      initialValue: _formData[name]?.toString(),
      decoration: InputDecoration(
        labelText: label,
        enabled: !isImmutable,
        alignLabelWithHint: true,
      ),
      maxLines:
          name.contains('prompt') ||
              name.contains('config') ||
              name.contains('kubeconfig')
          ? 5
          : 1,
      onSaved: (val) => _formData[name] = val,
      validator: isRequired
          ? (val) => (val == null || val.isEmpty) ? 'Required' : null
          : null,
    );
  }

  Widget _buildSelectField(
    String name,
    String label,
    List<SelectOption> options,
    bool isImmutable,
    bool isRequired,
  ) {
    return DropdownButtonFormField<String>(
      value: _formData[name],
      decoration: InputDecoration(labelText: label, enabled: !isImmutable),
      items: options
          .map(
            (opt) => DropdownMenuItem(value: opt.value, child: Text(opt.label)),
          )
          .toList(),
      onChanged: isImmutable
          ? null
          : (val) => setState(() => _formData[name] = val),
      validator: isRequired ? (val) => (val == null) ? 'Required' : null : null,
    );
  }

  Widget _buildRelationshipField(
    String name,
    String label,
    WidgetMetadata metadata,
    bool isImmutable,
    bool isRequired,
  ) {
    final options = _relationshipOptions[name] ?? [];
    final isMultiselect = metadata.multiselect ?? false;

    if (isMultiselect) {
      final List<dynamic> selectedValues =
          (_formData[name] as List<dynamic>?) ?? [];
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 8),
          if (options.isEmpty)
            const LinearProgressIndicator()
          else
            Wrap(
              spacing: 8,
              children: options.map((opt) {
                final id = opt[metadata.field ?? 'id'];
                final title = opt['title'] ?? opt['name'] ?? id.toString();
                final isSelected = selectedValues.contains(id);
                return FilterChip(
                  label: Text(title),
                  selected: isSelected,
                  onSelected: isImmutable
                      ? null
                      : (selected) {
                          setState(() {
                            if (selected) {
                              selectedValues.add(id);
                            } else {
                              selectedValues.remove(id);
                            }
                            _formData[name] = List.from(selectedValues);
                          });
                        },
                );
              }).toList(),
            ),
        ],
      );
    } else {
      return DropdownButtonFormField<dynamic>(
        value: _formData[name],
        decoration: InputDecoration(labelText: label, enabled: !isImmutable),
        items: options.map((opt) {
          final id = opt[metadata.field ?? 'id'];
          final title = opt['title'] ?? opt['name'] ?? id.toString();
          return DropdownMenuItem(value: id, child: Text(title));
        }).toList(),
        onChanged: isImmutable
            ? null
            : (val) => setState(() => _formData[name] = val),
        validator: isRequired
            ? (val) => (val == null) ? 'Required' : null
            : null,
      );
    }
  }

  Widget _buildRangeField(
    String name,
    String label,
    WidgetMetadata metadata,
    bool isImmutable,
    bool isRequired,
  ) {
    final min = metadata.min ?? 0.0;
    final max = metadata.max ?? 1.0;
    final value = (_formData[name] as num?)?.toDouble() ?? min;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: Theme.of(context).textTheme.bodySmall),
            Text(
              value.toStringAsFixed(2),
              style: Theme.of(
                context,
              ).textTheme.bodySmall?.copyWith(fontWeight: FontWeight.bold),
            ),
          ],
        ),
        Slider(
          value: value,
          min: min,
          max: max,
          onChanged: isImmutable
              ? null
              : (val) {
                  setState(() {
                    _formData[name] = val;
                  });
                },
        ),
      ],
    );
  }

  // Placeholder if needed for future
}
