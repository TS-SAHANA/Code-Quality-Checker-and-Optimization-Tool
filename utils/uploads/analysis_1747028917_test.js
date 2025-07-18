// This is a sample JavaScript file for testing code quality

function sayHello(name) {
    if (name === true) {
        console.log("Hello true");
    }

    let unusedVar = 5; // This variable is never used

    if (false) {
        console.log("This will never run");
    }

    var greeting = "Hello, " + name;
    console.log(greeting);
}

sayHello("Alice");
