document.addEventListener("DOMContentLoaded", function () {
    const inputs = document.querySelectorAll(".autogrow");
    if (!inputs.length) return;

    inputs.forEach(input => {
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");

    function px(n) {
        return Math.max(0, Math.round(n)) + "px";
    }

    function updateWidth() {
        const computed = getComputedStyle(input);
        ctx.font = computed.font;

        const text = input.value || input.placeholder || "";
        const textWidth = ctx.measureText(text).width;

        const paddingLeft = parseFloat(computed.paddingLeft) || 0;
        const paddingRight = parseFloat(computed.paddingRight) || 0;
        const borderLeft = parseFloat(computed.borderLeftWidth) || 0;
        const borderRight = parseFloat(computed.borderRightWidth) || 0;

        const extra = 0;
        const desired = textWidth + paddingLeft + paddingRight + borderLeft + borderRight + extra;

        const minW = parseFloat(computed.minWidth) || 100;
        const maxW = parseFloat(computed.maxWidth) || 700;
        input.style.width = px(Math.min(Math.max(desired, minW), maxW));
    }

    ["input", "change", "keyup"].forEach(ev => input.addEventListener(ev, updateWidth));
    window.addEventListener("resize", updateWidth);

    updateWidth(); // initial sizing
    });
});
