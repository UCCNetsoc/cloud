import { Box, Button, ScrollArea, Text, Textarea, TextInput } from "@mantine/core";
import { useForm } from "@mantine/form";
import { useState } from "react";
import { Cloud } from "../types";
import ModalTop from "./ModalTop";

const InstanceRequest = (props: { templates: Cloud.Template[] | null }) => {
  const [metaData, setMetaData] = useState<Cloud.TemplateMetadata | null>(null);
  const [breadcrumbs, setBreadcrumbs] = useState<JSX.Element[]>([]);

  const [selectedTemplate, setSelectedTemplate] = useState<Cloud.Template | null>(null);
  const [hostname, setHostname] = useState<string | null>(null);
  const [reason, setReason] = useState<string | null>(null);

  const form = useForm<{ template_id: number, hostname: string, reason: string, }>({
    initialValues: {
      template_id: 0,
      hostname: "",
      reason: "",
    }
  })

  if (props.templates !== null) {
    return (
      <>
        <ModalTop />
        <div style={{ height: "600px", paddingTop: "1em" }}>
          <div style={{ display: "flex", maxHeight: "600px", float: "left" }}>
            <ScrollArea style={{
              width: "40%",
              height: "600px",
            }}>
              {props.templates ? props.templates.map((template, index) => {
                return (
                  <Box
                    key={index}
                    sx={(theme) => ({
                      backgroundColor: theme.colorScheme === 'dark' ? selectedTemplate === props.templates![index] ? theme.colors.dark[4] : theme.colors.dark[7] : theme.colors.gray[0],
                      padding: theme.spacing.xl,
                      borderRadius: theme.radius.md,
                      cursor: 'pointer',
                      width: "100%",

                      '&:hover': {
                        backgroundColor:
                          theme.colorScheme === 'dark' ? theme.colors.dark[5] : theme.colors.gray[1],
                      },
                    })}
                    onClick={() => {
                      setMetaData(template.metadata);
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "flex-start" }}>
                      <img src={template.metadata.logo_url} style={{ maxWidth: "32px", marginRight: "1em" }} />
                      {template.metadata.title}
                    </div>
                    <small style={{ display: "block" }}>{template.specs.cores} CPU, {template.specs.memory} RAM, {template.specs.disk_space}GB Disk</small>
                  </Box>
                )
              }) : null}
            </ScrollArea>
            <ScrollArea style={{ height: "600px", width: "200px", display: "flex", flexDirection: "column", alignItems: "center", borderLeft: `1px solid white`, padding: "1em 0 4em 0em" }}>
              <div>
                <div style={{ paddingBottom: "2em" }}>
                  <span style={{ display: "flex", alignItems: "center" }}>
                    {metaData?.logo_url ? <img src={metaData?.logo_url} style={{ maxWidth: "30%", marginRight: "1em" }} /> : null}
                    <h2>{metaData?.title || "Select a template to continue"}</h2>
                  </span>
                  <Text style={{
                    whiteSpace: "pre",
                  }}>
                    {metaData?.subtitle || "A template represents a base installation for your new instance."}
                  </Text>
                  <p style={{ width: "200px", wordBreak: "break-all" }}>
                    {metaData?.description}
                  </p>
                </div>
              </div>
              {metaData ?
                <div style={{ marginTop: "2em", width: "100%" }}>
                  <TextInput style={{ width: "100%", maxWidth: "300px", marginBottom: "2em" }} label="Hostname" placeholder="hostname" onChange={(e) => setHostname(e.currentTarget.value)} rightSection={<p style={{ width: "100px", whiteSpace: "nowrap" }}>.netsoc.cloud</p>} />
                  <Textarea label="Why do you want this instance?" minRows={6} />
                </div> : null}
            </ScrollArea>
          </div>
        </div>
      </>
    )
  } else {
    return (
      <div>
        Loading...
      </div>
    )
  }
}

export default InstanceRequest;
