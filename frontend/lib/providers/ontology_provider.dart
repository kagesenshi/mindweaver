import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/ontology.dart';
import 'api_providers.dart';

class OntologyListNotifier extends StateNotifier<AsyncValue<List<Ontology>>> {
  final Ref ref;

  OntologyListNotifier(this.ref) : super(const AsyncValue.loading()) {
    loadOntologies();
  }

  Future<void> loadOntologies() async {
    state = const AsyncValue.loading();
    try {
      final client = ref.read(apiClientProvider);
      final response = await client.listAll(
        '/api/v1/ontologies',
        (json) => Ontology.fromJson(json as Map<String, dynamic>),
      );
      state = AsyncValue.data(response);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> createOntology(Ontology ontology) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.post(
        '/api/v1/ontologies',
        ontology.toJson(),
        (json) => Ontology.fromJson(json as Map<String, dynamic>),
      );
      await loadOntologies();
    } catch (e) {
      rethrow;
    }
  }

  Future<void> deleteOntology(int id) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.delete('/api/v1/ontologies/$id');
      await loadOntologies();
    } catch (e) {
      rethrow;
    }
  }
}

final ontologyListProvider =
    StateNotifierProvider<OntologyListNotifier, AsyncValue<List<Ontology>>>((
      ref,
    ) {
      return OntologyListNotifier(ref);
    });
