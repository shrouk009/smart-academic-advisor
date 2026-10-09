function loginStudent() {

    const name =
        document
        .getElementById(
            "studentName"
        )
        .value
        .trim();


    const email =
        document
        .getElementById(
            "email"
        )
        .value
        .trim();


    const password =
        document
        .getElementById(
            "password"
        )
        .value
        .trim();


    const errorBox =
        document
        .getElementById(
            "loginError"
        );


    errorBox.innerText =
        "";


    if (
        !name
        ||
        !email
        ||
        !password
    ) {

        errorBox.innerText =
            "Please enter your name, email and password.";

        return;
    }


    if (
        !email.includes("@")
    ) {

        errorBox.innerText =
            "Please enter a valid university email.";

        return;
    }


    localStorage.setItem(
        "studentLoggedIn",
        "true"
    );


    localStorage.setItem(
        "studentEmail",
        email
    );


    localStorage.setItem(
        "studentName",
        name
    );


    window.location.href =
        "index.html";
}