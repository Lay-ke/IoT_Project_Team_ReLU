import { Accordion } from "@/components/ui/accordion";
import { useMaintenanceSchedules } from "@/hooks/useMaintenanceSchedules";
import { MaintenanceScheduleCard } from "./MaintenanceScheduleCard";

const priorityOrder = {
  immediate: 1,
  scheduled: 2,
  deferred: 3,
};

const severityOrder = {
  critical: 1,
  warning: 2,
  monitor: 3,
  low: 4,
};

export const MaintenanceScheduleList = () => {
  const { data: schedules, isLoading, error } = useMaintenanceSchedules();

  if (isLoading) {
    return (
        <div className="text-center p-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground text-sm">Loading maintenance schedules...</p>
        </div>
    );
  }

  if (error) {
    return <div className="text-destructive p-8">Error loading maintenance schedules: {error.message}</div>;
  }

  const sortedSchedules = [...(schedules || [])].sort((a, b) => {
    const priorityA = priorityOrder[a.content.fault_details.priority as keyof typeof priorityOrder] || 99;
    const priorityB = priorityOrder[b.content.fault_details.priority as keyof typeof priorityOrder] || 99;
    if (priorityA !== priorityB) return priorityA - priorityB;

    const severityA = severityOrder[a.content.fault_details.severity as keyof typeof severityOrder] || 99;
    const severityB = severityOrder[b.content.fault_details.severity as keyof typeof severityOrder] || 99;
    if (severityA !== severityB) return severityA - severityB;

    return new Date(a.content.scheduling_info.action_required_by).getTime() - new Date(b.content.scheduling_info.action_required_by).getTime();
  });

  return (
    <div className="space-y-4">
        <h2 className="text-2xl font-bold text-foreground px-3">Maintenance Schedules</h2>
        {sortedSchedules.length > 0 ? (
            <Accordion type="multiple" className="space-y-2">
                {sortedSchedules.map((schedule) => (
                    <MaintenanceScheduleCard key={schedule.key} schedule={schedule.content} />
                ))}
            </Accordion>
        ) : (
            <p className="text-muted-foreground p-8 text-center">No maintenance schedules found.</p>
        )}
    </div>
  );
};
