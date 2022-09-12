import { ActionIcon, Drawer, Skeleton, Table, ThemeIcon, Tooltip, useMantineTheme } from "@mantine/core";
import { IconBrandDocker, IconPlayerPlay, IconPlayerStop, IconServer } from "@tabler/icons";
import { useEffect, useState } from "react";
import { GetInstances } from "../api";
import { Cloud } from "../types";
import InstanceEdit from "./InstanceEdit";
import ResourceRing from "./ResourceRing";

const InstanceTable = () => {
  const [initialLoading, setInitialLoading] = useState(true);
  const [opened, setOpened] = useState(false);
  const [selected, setSelected] = useState<number | null>(null);
  const [vpsInstances, setVpsInstances] = useState<Cloud.Instance[]>([]);
  const [lxcInstances, setLxcInstances] = useState<Cloud.Instance[]>([]);

  const [instances, setInstances] = useState<Cloud.Instance[]>([]);

  const theme = useMantineTheme();

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
    const params = new URLSearchParams(window.location.search)
    if (params.has("q")) {
      if (params.get("q") !== null && parseInt(params.get("q") as string)) {
        setSelected(parseInt(params.get("q") || "0"))
      }
    }
  }, [])

  // useEffect(() => {
  //   setInstances([...lxcInstances, ...vpsInstances]);
  // }, [lxcInstances, vpsInstances])

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

        return (<tr onClick={
          () => {
            setSelected(index);
            setOpened(true);
          }
        } key={instance.id} style={{ borderLeft: "1px solid", borderColor: instance.status === "Running" ? '#0000' : theme.colors.red[7], cursor: "pointer", padding: "4em" }}
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
          <td>
            <Tooltip label={instance.status === "Running" ? "Stop" : "Start"}>
              <ActionIcon onClick={(event: any) => {
                alert("bruh")
                event?.stopPropagation();
              }}>
                {instance.status === "Stopped" ? <IconPlayerPlay color="#1f4" /> :
                  <IconPlayerStop color="#f33" />}
              </ActionIcon>
            </Tooltip>
          </td>
        </tr>
        )
      })}
    </>
  )

  return (
    <div>
      <h1>Instances</h1>
      {initialLoading ? (
        <>
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
        </>
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
        onClose={() => setOpened(false)}
        padding="xs"
      >
        <InstanceEdit instance={instances[selected!]} />
      </Drawer>
    </div >
  )
}

export default InstanceTable;
