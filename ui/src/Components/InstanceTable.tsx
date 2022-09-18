import { ActionIcon, Button, Drawer, Modal, Skeleton, Table, ThemeIcon, Tooltip, useMantineTheme } from "@mantine/core";
import { IconBrandDocker, IconPlayerPlay, IconPlayerStop, IconPlus, IconRefresh, IconServer } from "@tabler/icons";
import { useContext, useEffect, useLayoutEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { GetAllTemplates, GetTemplates } from "../api/template";
// import { GetInstances } from "../api";
import { DesktopContext, InstanceContext, InstanceTemplateContext } from "../App";
import { Cloud } from "../types";
import InstanceEdit from "./InstanceEdit";
import InstanceRequest from "./InstanceRequest";
import ResourceRing from "./ResourceRing";

const InstanceTable = () => {
  const [initialLoading, setInitialLoading] = useState(false);
  const [opened, setOpened] = useState(false);
  const [requestOpened, setRequestOpened] = useState(false);
  const [selected, setSelected] = useState<number | null>(null);
  // const [templates, setTemplates] = useState<Cloud.Template[]>([] as Cloud.Template[]);

  const { instances, setInstances } = useContext(InstanceContext);
  const [deactivations, setDeactivations] = useState<Deactivation[]>([])

  const location = useLocation();

  const theme = useMantineTheme();

  interface Deactivation {
    str: string,
    past: boolean,
  }

  // useEffect(() => {
  //   console.log(instances)
  // }, [instances])

  // useEffect(() => {
  //   (async () => {
  //     const tmp_lxcInstances = await GetInstances(Cloud.Type.LXC);
  //     // setLxcInstances(tmp_lxcInstances ? Object.values(tmp_lxcInstances) : []);

  //     const tmp_VpsInstances = await GetInstances(Cloud.Type.VPS);

  //     // setVpsInstances(tmp_VpsInstances ? Object.values(tmp_VpsInstances) : []);
  //     setInstances([...tmp_lxcInstances ? Object.values(tmp_lxcInstances) : [], ...tmp_VpsInstances ? Object.values(tmp_VpsInstances) : []]);
  //     setInitialLoading(false);
  //   })();
  // }, [])

  const { instanceTemplates, setInstanceTemplates } = useContext(InstanceTemplateContext)

  const desktop = useContext(DesktopContext)

  useEffect(() => {
    (async () => {
      if (instanceTemplates === null) {
        setInstanceTemplates(await GetAllTemplates());
      }
      // setTemplates(tmp_templates ? Object.values(tmp_templates) : []);
    })();
  }, []);

  useEffect(() => {
    if (instances) {
      const params = location.search;
      const instance_id = parseInt(params.split("q=")[1])

      if (instance_id) {
        const instance_index = instances.findIndex((instance) => instance.id === instance_id)
        setSelected(instance_index)
        setOpened(true)
      }

      const deltas: Deactivation[] = [];
      for (var i = 0; i < instances.length; i++) {
        const date = new Date(instances[i].inactivity_shutdown_date);
        const formatter = new Intl.RelativeTimeFormat("en", { numeric: "auto" })

        const dateDelta = (date.getTime() - Date.now()) / (1000 * 3600 * 24)
        deltas.push({
          str: formatter.format(Math.round(dateDelta), 'day'),
          past: dateDelta < 0
        })
      }

      setDeactivations(deltas)
    }
  }, [instances])

  useEffect(() => {
    if (selected !== null) {
      setOpened(true)
    }
  }, [selected])

  if (instances !== null) {
    const table_rows = (
      <>
        {instances.map((instance, index) => {
          const disk_available = instance.disk > 0
          const mem_available = instance.mem > 0

          return (
            <tr onClick={instance.active ?
              () => {
                setSelected(index);
                setOpened(true);
                window.history.replaceState(null, instance.hostname, `?q=${instance.id}`)
              } : () => { }
            } key={instance.id} style={{ borderLeft: "1px solid", borderColor: instance.status === "Running" ? '#0000' : theme.colors.red[7], cursor: instance.active ? "pointer" : "default", padding: "4em", color: !instance.active ? theme.colorScheme == "dark" ? theme.colors.gray[7] : theme.colors.gray[4] : "unset" }}
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
                <Tooltip label={!instance.active ? "Reactivate" : instance.status === "Running" ? "Stop" : "Start"}>
                  <ActionIcon>
                    {!instance.active ?
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
        {initialLoading === false && instances === null ? (
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
                  <th>
                    <ActionIcon>
                      <IconPlus />
                    </ActionIcon>
                  </th>
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
                <th style={{ width: "250px" }}>
                  <Button leftIcon={<IconPlus />} onClick={() => {
                    setRequestOpened(true)
                  }}>
                    Request Instance
                  </Button>
                </th>
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
          withinPortal={false}
          overlayBlur={1}
          style={{
            height: "100%",
            maxHeight: "unset",
          }}
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
        <Modal fullScreen={!desktop} centered style={{ padding: 0, overflowX: "hidden" }} size="1000px" opened={requestOpened} onClose={() => { setRequestOpened(false) }}>
          <InstanceRequest templates={instanceTemplates} />
        </Modal>
      </div >
    )
  } else {
    return (<></>)
  }
}

export default InstanceTable;
