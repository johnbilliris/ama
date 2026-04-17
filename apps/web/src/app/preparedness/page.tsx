import { OperatingModelAnalyzer } from "../../components/preparedness/operating-model-analyzer";
import { listPreparednessFrameworks } from "../../lib/api/frameworks";
import { listPreparednessOrganisations } from "../../lib/api/organisations";

export default async function PreparednessPage() {
  const [organisations, frameworks] = await Promise.all([
    listPreparednessOrganisations("nsw").catch(() => []),
    listPreparednessFrameworks("nsw").catch(() => []),
  ]);

  return (
    <div className="incident-page">
      <OperatingModelAnalyzer organisations={organisations} frameworks={frameworks} />
    </div>
  );
}
