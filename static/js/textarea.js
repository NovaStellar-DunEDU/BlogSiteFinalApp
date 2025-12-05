document.addEventListener("DOMContentLoaded", function () {
    const textareas = document.querySelectorAll(".growtextarea");

    textareas.forEach(textarea => {
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");

        function resize() {
            const computed = getComputedStyle(textarea);
            ctx.font = computed.font;

            const text = textarea.value || textarea.placeholder || "";
            const textWidth = ctx.measureText(text).width;

            const paddingLeft = parseFloat(computed.paddingLeft) || 0;
            const paddingRight = parseFloat(computed.paddingRight) || 0;
            const borderLeft = parseFloat(computed.borderLeftWidth) || 0;
            const borderRight = parseFloat(computed.borderRightWidth) || 0;

            const desiredWidth = textWidth + paddingLeft + paddingRight + borderLeft + borderRight;

            const minW = parseFloat(computed.minWidth) || 150;
            const maxW = parseFloat(computed.maxWidth) || 600;

            const finalWidth = Math.min(Math.max(desiredWidth, minW), maxW);

            textarea.style.width = finalWidth + "px";

            if (finalWidth >= maxW) {
                textarea.style.height = "auto";
                textarea.style.height = textarea.scrollHeight + "px";
            } else {
                textarea.style.height = computed.minHeight || "10px"; // then grow vertically
        }
    }

    textarea.addEventListener("input", resize);
    window.addEventListener("resize", resize);

    resize();
    });
});
