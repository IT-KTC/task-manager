document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll(".auth-password-toggle");

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const wrapper = button.closest(".auth-password-wrap");

      const input = wrapper?.querySelector("input");

      if (!input) return;

      const isHidden = input.type === "password";

      input.type = isHidden ? "text" : "password";

      button.setAttribute("aria-pressed", String(isHidden));

      button.setAttribute(
        "aria-label",
        isHidden ? "Ẩn mật khẩu" : "Hiện mật khẩu",
      );
    });
  });
});
