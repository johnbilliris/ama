// Allow TypeScript to understand CSS file imports
declare module "*.css" {
  const styles: Record<string, string>;
  export default styles;
}
