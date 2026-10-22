import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { ArrowUpIcon } from "./Icons";

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
}

/** Строка ввода: растёт по высоте, Enter — отправить, Shift+Enter — новая строка. */
export function Composer({ onSend, disabled }: Props) {
  const [text, setText] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 220) + "px";
  }, [text]);

  useEffect(() => ref.current?.focus(), []);

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    const t = text.trim();
    if (!t || disabled) return;
    onSend(t);
    setText("");
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <form className="composer" onSubmit={submit}>
      <textarea
        ref={ref}
        rows={1}
        value={text}
        placeholder="Опишите, что произошло…"
        onChange={(e) => setText(e.target.value)}
        onKeyDown={onKeyDown}
      />
      <button className="send" type="submit" disabled={disabled || !text.trim()} title="Отправить">
        <ArrowUpIcon />
      </button>
    </form>
  );
}
