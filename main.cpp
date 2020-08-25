

#include <iostream>
#include "calculator.h"

using namespace::std;

int main() {

	double x, y, result;
	char oper;

	calculator c;

	cout << "Calculator Console Application" << endl;
	cout << "Please enter operation: " << endl;

	while (true) {
		cin >> x >> oper >> y;
		result = c.Calculate(x, oper, y);
		cout << "Result is: " << result << endl;
	}

	return 0;
}