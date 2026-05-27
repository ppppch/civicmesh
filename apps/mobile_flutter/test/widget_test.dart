import 'package:flutter_test/flutter_test.dart';

import 'package:civicgrid_mobile/main.dart';

void main() {
  testWidgets('CivicGrid mobile app renders', (WidgetTester tester) async {
    await tester.pumpWidget(const CivicGridMobileApp());
    expect(find.text('CivicGrid NYC Mobile'), findsOneWidget);
  });
}
