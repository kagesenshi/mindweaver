class User {
  final int id;
  final String email;
  final String? preferredUsername;
  final String? displayName;
  final String? picture;

  User({
    required this.id,
    required this.email,
    this.preferredUsername,
    this.displayName,
    this.picture,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      email: json['email'],
      preferredUsername: json['preferred_username'],
      displayName: json['display_name'],
      picture: json['picture'],
    );
  }

  String get name => displayName ?? preferredUsername ?? email.split('@')[0];
}
