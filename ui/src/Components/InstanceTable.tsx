import { ActionIcon, Drawer, Skeleton, Table, ThemeIcon, Tooltip, useMantineTheme } from "@mantine/core";
import { IconBrandDocker, IconPlayerPlay, IconPlayerStop, IconRefresh, IconServer } from "@tabler/icons";
import { time } from "console";
import { useEffect, useState } from "react";
import { GetInstances } from "../api";
import { Cloud } from "../types";
import InstanceEdit from "./InstanceEdit";
import ResourceRing from "./ResourceRing";

const InstanceTable = () => {
  const [initialLoading, setInitialLoading] = useState(true);
  const [opened, setOpened] = useState(false);
  const [selected, setSelected] = useState<number | null>(null);

  const [instances, setInstances] = useState<Cloud.Instance[]>([]);
  const [deactivations, setDeactivations] = useState<Deactivation[]>([])

  const theme = useMantineTheme();

  interface Deactivation {
    str: string,
    past: boolean,
  }

  useEffect(() => {
    (async () => {
      const tmp_lxcInstances = await GetInstances(Cloud.Type.LXC);
      // setLxcInstances(tmp_lxcInstances ? Object.values(tmp_lxcInstances) : []);

      const tmp_VpsInstances = await GetInstances(Cloud.Type.VPS);
      // setVpsInstances(tmp_VpsInstances ? Object.values(tmp_VpsInstances) : []);
      setInstances([...tmp_lxcInstances ? Object.values(tmp_lxcInstances) : [], ...tmp_VpsInstances ? Object.values(tmp_VpsInstances) : []])
      setInitialLoading(false);
    })();
  }, [])

  useEffect(() => {
    const deltas: Deactivation[] = [];
    for (var i = 0; i<instances.length; i++) {
      console.log(instances[i].inactivity_shutdown_date)
      const date = new Date(instances[i].inactivity_shutdown_date);
      const formatter = new Intl.RelativeTimeFormat("en", { numeric: "auto" })

      const dateDelta = (date.getTime() - Date.now()) / (1000 * 3600 * 24)
      deltas.push({
        str: formatter.format(Math.round(dateDelta), 'day'),
        past: dateDelta < 0
      })
    }

    setDeactivations(deltas)
  }, [instances])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    if (params.has("q")) {
      if (params.get("q") !== null && parseInt(params.get("q") as string)) {
        setSelected(parseInt(params.get("q") || "0"))
      }
    }
  }, [])

  useEffect(() => {
    if (selected !== null) {
      setOpened(true)
    }
  }, [selected])

  const table_rows = (
    <>
      {instances.map((instance, index) => {
        const disk_available = instance.disk > 0
        const mem_available = instance.mem > 0

        return (
          <tr onClick={ instance.active ?
            () => {
              setSelected(index);
              setOpened(true);
            } : () => {}
          } key={instance.id} style={{ borderLeft: "1px solid", borderColor: instance.status === "Running" ? '#0000' : theme.colors.red[7], cursor: instance.active ? "pointer" : "default", padding: "4em", color: !instance.active ? theme.colorScheme == "dark" ? theme.colors.gray[7] : theme.colors.gray[4] : "unset"}}
          >
            <td>
              <span style={{ display: 'flex', alignItems: 'center' }}>
                {instance.type.toUpperCase()}
                <ThemeIcon style={{ margin: "0 1em" }} color={instance.status === "Running" ? "green" : "red"}>
                  {instance.type === Cloud.Type.LXC ? <IconBrandDocker /> : <IconServer />}
                </ThemeIcon>
              </span>
            </td>
            <td>{instance.hostname}</td>
            <td>{
              (instance.uptime ? (instance.uptime / 60 / 60 + 1).toFixed(0).toString() + " hours" : "N/A")
            }</td>
            <td>{instance.specs.cores}</td>

            <td>{!mem_available ? "N/A" : <span style={{ display: "flex", alignItems: "center" }}>{<ResourceRing label="" current={instance.mem} max={instance.specs.memory * 10000} size={32} outsidelabel={(instance.specs.memory / 1024).toString()} decimals={0} />}</span>}</td>
            <td>{!disk_available ? "N/A" : <span style={{ display: "flex", alignItems: "center" }}>{<ResourceRing label="" current={instance.disk} max={instance.specs.disk_space * 10000000} size={32} outsidelabel={(instance.specs.disk_space).toString()} decimals={0} />}</span>}</td>
            <td>{instance.status}</td>
            <td style={{ color: theme.colorScheme === "dark" ? "white" : "black" }}>{
              instance.metadata.permanent ? 
              <>
                Permanent
              </> : 
              <>
                {deactivations[index]?.past ? "Deactivated" : "Deactivation"} {deactivations[index]?.str}
              </>
            }</td>
            <td>
              <Tooltip label={!instance.active ? "Reactivate" :  instance.status === "Running" ? "Stop" : "Start"}>
                <ActionIcon>
                  { !instance.active ? 
                    <IconRefresh color={theme.colors.blue[4]} />
                    : instance.status === "Running" ?
                      <IconPlayerStop color={theme.colors.red[6]} /> : <IconPlayerPlay color={theme.colors.green[6]} />
                  }
                </ActionIcon>
              </Tooltip>
            </td>
          </tr>
          )
        })
      }
    </>
  )

  return (
    <div>
      <h1>Instances</h1>
      {initialLoading ? (
        <div style={{ minWidth: "800px" }}>
          <Table verticalSpacing="sm">
            <thead>
              <tr>
                <th>Type</th>
                <th>Name</th>
                <th>Uptime</th>
                <th>CPU Cores</th>
                <th>Memory</th>
                <th>Disk Usage</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {Array(6).fill(0).map((_, index) => (
                <tr key={index}>
                  <td><Skeleton height={32} /></td>
                  <td><Skeleton height={32} /></td>
                  <td><Skeleton height={32} /></td>
                  <td><Skeleton height={32} /></td>
                  <td><Skeleton height={32} /></td>
                  <td><Skeleton height={32} /></td>
                  <td><Skeleton height={32} /></td>
                  <td><Skeleton height={32} /></td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      ) : (<div>
        <Table verticalSpacing="sm" highlightOnHover>
          <thead>
            <tr>
              <th>Type</th>
              <th>Name</th>
              <th>Uptime</th>
              <th>CPU Cores</th>
              <th>Memory</th>
              <th>Disk Usage</th>
              <th>Status</th>
              <th>Activation</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {/* {lxc_rows} */}
            {table_rows}
            {/* {vps_rows} */}
          </tbody>
        </Table>
      </div >
      )}
      <Drawer
        position="right"
        size="800px"
        opened={opened}
        onClose={() => {
          setOpened(false); 
          setSelected(null)
        }}
        padding="xs"
      >
        <InstanceEdit instance={instances[selected!]} />
      </Drawer>
    </div >
  )
}

export default InstanceTable;
