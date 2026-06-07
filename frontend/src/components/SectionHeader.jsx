export default function SectionHeader({ eyebrow, title, subtitle, actionLabel, onAction }) {
  return (
    <div className="section-header">
      <div>
        {eyebrow ? <span className="eyebrow">{eyebrow}</span> : null}
        <h2>{title}</h2>
        {subtitle ? <p>{subtitle}</p> : null}
      </div>
      {actionLabel ? (
        <button type="button" className="secondary-button" onClick={onAction}>{actionLabel}</button>
      ) : null}
    </div>
  );
}
