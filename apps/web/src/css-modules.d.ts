// Allow TypeScript to understand CSS file imports (e.g. azure-maps-control styles)
declare module "*.css" {
  const styles: Record<string, string>;
  export default styles;
}
