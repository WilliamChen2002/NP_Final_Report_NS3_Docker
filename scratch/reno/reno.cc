#include "ns3/applications-module.h"
#include "ns3/core-module.h"
// new flow mointor
#include "ns3/flow-monitor-module.h"
#include "ns3/internet-module.h"
#include "ns3/network-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/traffic-control-module.h"

#include <fstream>
#include <iostream>
#include <string>
#include <sys/stat.h>

using namespace ns3;
// 本程式碼修改自範例tcp-linux-reno，大部分維持原狀，改變實驗變數與輸出位址

// 輸出全域變數
std::string dir = "output/reno/";
Time stopTime = Seconds(60.1);
uint32_t segmentSize = 1460;

// throughput 用
uint32_t prev_bytes = 0;
Time prevTime;

// 輸出串流
std::ofstream fPlotQueue;
std::ofstream fPlotCwnd;
std::ofstream fPlotThroughput;

// 確認Router 1的queue length
void CheckQueueSize(Ptr<QueueDisc> queue) {
  uint32_t qSize = queue->GetCurrentSize().GetValue();

  Simulator::Schedule(Seconds(0.2), &CheckQueueSize, queue);
  fPlotQueue << Simulator::Now().GetSeconds() << " " << qSize << std::endl;
}

// 追蹤throughput
static void TraceThroughput(Ptr<FlowMonitor> monitor) {
  FlowMonitor::FlowStatsContainer stats = monitor->GetFlowStats();
  if (!stats.empty()) {
    auto itr = stats.begin();
    Time curTime = Now();
    fPlotThroughput << curTime.GetSeconds() << " "
                    << 8 * (itr->second.txBytes - prev_bytes) /
                           ((curTime - prevTime).ToDouble(Time::US))
                    << std::endl;
    prevTime = curTime;
    prev_bytes = itr->second.txBytes;
  }
  Simulator::Schedule(Seconds(0.2), &TraceThroughput, monitor);
}

// 追蹤node 0的cwnd值
static void CwndChange(uint32_t oldCwnd, uint32_t newCwnd) {
  fPlotCwnd << Simulator::Now().GetSeconds() << " " << newCwnd / segmentSize
            << std::endl;
}

// 追蹤queue的drop事件
static void DropAtQueue(Ptr<OutputStreamWrapper> stream,
                        Ptr<const QueueDiscItem> item) {
  *stream->GetStream() << Simulator::Now().GetSeconds() << " 1" << std::endl;
}

// 追蹤cwnd值變化
void TraceCwnd(uint32_t node, uint32_t cwndWindow,
               Callback<void, uint32_t, uint32_t> CwndTrace) {
  Config::ConnectWithoutContext(
      "/NodeList/" + std::to_string(node) + "/$ns3::TcpL4Protocol/SocketList/" +
          std::to_string(cwndWindow) + "/CongestionWindow",
      CwndTrace);
}

// 安裝BulkSend應用程式
void InstallBulkSend(Ptr<Node> node, Ipv4Address address, uint16_t port,
                     std::string socketFactory, uint32_t nodeId,
                     uint32_t cwndWindow,
                     Callback<void, uint32_t, uint32_t> CwndTrace) {
  BulkSendHelper source(socketFactory, InetSocketAddress(address, port));
  source.SetAttribute("MaxBytes", UintegerValue(0));
  ApplicationContainer sourceApps = source.Install(node);
  sourceApps.Start(Seconds(0.1));
  Simulator::Schedule(Seconds(0.1) + Seconds(0.001), &TraceCwnd, nodeId,
                      cwndWindow, CwndTrace);
  sourceApps.Stop(stopTime);
}

// 安裝PacketSink應用程式
void InstallPacketSink(Ptr<Node> node, uint16_t port,
                       std::string socketFactory) {
  PacketSinkHelper sink(socketFactory,
                        InetSocketAddress(Ipv4Address::GetAny(), port));
  ApplicationContainer sinkApps = sink.Install(node);
  sinkApps.Start(Seconds(0.1));
  sinkApps.Stop(stopTime);
}

int main(int argc, char *argv[]) {
  uint32_t stream = 1;
  std::string socketFactory = "ns3::TcpSocketFactory";
  std::string tcpTypeId = "ns3::TcpLinuxReno";
  std::string qdiscTypeId = "ns3::FifoQueueDisc";
  bool isSack = true;
  uint32_t delAckCount = 1;
  std::string recovery = "ns3::TcpClassicRecovery";
  // 命令參數綁定，使我們可以更換TCP變體、queue discipline、segment
  // size、delayed ack count、是否啟用SACK、模擬結束時間以及recovery algorithm
  // CommandLine cmd(__FILE__);
  // cmd.AddValue(
  //     "tcpTypeId",
  //     "TCP variant to use (e.g., ns3::TcpNewReno, ns3::TcpLinuxReno, etc.)",
  //     tcpTypeId);
  // cmd.AddValue("qdiscTypeId",
  //              "Queue disc for gateway (e.g., ns3::CoDelQueueDisc)",
  //              qdiscTypeId);
  // cmd.AddValue("segmentSize", "TCP segment size (bytes)", segmentSize);
  // cmd.AddValue("delAckCount", "Delayed ack count", delAckCount);
  // cmd.AddValue("enableSack", "Flag to enable/disable sack in TCP", isSack);
  // cmd.AddValue("stopTime",
  //              "Stop time for applications / simulation time will be
  //              stopTime", stopTime);
  // cmd.AddValue("recovery",
  //              "Recovery algorithm type to use (e.g., ns3::TcpPrrRecovery",
  //              recovery);
  // cmd.Parse(argc, argv);

  // 確認TCP變體與queue discipline的TypeId是否存在
  TypeId qdTid;
  NS_ABORT_MSG_UNLESS(TypeId::LookupByNameFailSafe(qdiscTypeId, &qdTid),
                      "TypeId " << qdiscTypeId << " not found");

  // 設定TCP的Recovery Algorithm
  Config::SetDefault("ns3::TcpL4Protocol::RecoveryType",
                     TypeIdValue(TypeId::LookupByName(recovery)));
  TypeId tcpTid;
  NS_ABORT_MSG_UNLESS(TypeId::LookupByNameFailSafe(tcpTypeId, &tcpTid),
                      "TypeId " << tcpTypeId << " not found");
  Config::SetDefault("ns3::TcpL4Protocol::SocketType",
                     TypeIdValue(TypeId::LookupByName(tcpTypeId)));

  // 創建節點
  NodeContainer leftNodes;
  NodeContainer rightNodes;
  NodeContainer routers;
  routers.Create(2);
  leftNodes.Create(1);
  rightNodes.Create(1);

  std::vector<NetDeviceContainer> leftToRouter;
  std::vector<NetDeviceContainer> routerToRight;

  // 創建router之間的point-to-point link
  PointToPointHelper pointToPointRouter;
  // pointToPointRouter.SetDeviceAttribute("DataRate", StringValue("1Mbps"));
  // pointToPointRouter.SetChannelAttribute("Delay", StringValue("10ms"));
  pointToPointRouter.SetDeviceAttribute("DataRate", StringValue("10Mbps"));
  pointToPointRouter.SetChannelAttribute("Delay", StringValue("20ms"));
  NetDeviceContainer r1r2ND =
      pointToPointRouter.Install(routers.Get(0), routers.Get(1));

  // 創建point-to-point link helpers並連接leaf nodes到router
  PointToPointHelper pointToPointLeaf;
  pointToPointLeaf.SetDeviceAttribute("DataRate", StringValue("15Mbps"));
  pointToPointLeaf.SetChannelAttribute("Delay", StringValue("1ms"));
  leftToRouter.push_back(
      pointToPointLeaf.Install(leftNodes.Get(0), routers.Get(0)));
  routerToRight.push_back(
      pointToPointLeaf.Install(routers.Get(1), rightNodes.Get(0)));

  InternetStackHelper internetStack;

  internetStack.Install(leftNodes);
  internetStack.Install(rightNodes);
  internetStack.Install(routers);

  // 為每個interface分配IP地址
  Ipv4AddressHelper ipAddresses("10.0.0.0", "255.255.255.0");

  Ipv4InterfaceContainer r1r2IPAddress = ipAddresses.Assign(r1r2ND);
  ipAddresses.NewNetwork();

  std::vector<Ipv4InterfaceContainer> leftToRouterIPAddress;
  leftToRouterIPAddress.push_back(ipAddresses.Assign(leftToRouter[0]));
  ipAddresses.NewNetwork();

  std::vector<Ipv4InterfaceContainer> routerToRightIPAddress;
  routerToRightIPAddress.push_back(ipAddresses.Assign(routerToRight[0]));

  Ipv4GlobalRoutingHelper::PopulateRoutingTables();

  // 設定TCP的發送與接收緩衝區大小
  Config::SetDefault("ns3::TcpSocket::SndBufSize", UintegerValue(1 << 20));
  Config::SetDefault("ns3::TcpSocket::RcvBufSize", UintegerValue(1 << 20));

  // 設定TCP的初始cwnd值
  Config::SetDefault("ns3::TcpSocket::InitialCwnd", UintegerValue(10));

  // 設定TCP的delayed ack count
  Config::SetDefault("ns3::TcpSocket::DelAckCount", UintegerValue(delAckCount));

  // 設定TCP的segment size
  Config::SetDefault("ns3::TcpSocket::SegmentSize", UintegerValue(segmentSize));

  // 啟用/禁用TCP的SACK選項
  Config::SetDefault("ns3::TcpSocketBase::Sack", BooleanValue(isSack));

  // 安裝FlowMonitor以追蹤流量資訊
  FlowMonitorHelper flowmon;
  Ptr<FlowMonitor> monitor = flowmon.InstallAll();

  // 確認輸出資料夾是否存在，若存在則刪除後重新創建
  struct stat buffer;
  int retVal [[maybe_unused]];
  if ((stat(dir.c_str(), &buffer)) == 0) {
    std::string dirToRemove = "rm -rf " + dir;
    retVal = system(dirToRemove.c_str());
    NS_ASSERT_MSG(retVal == 0, "Error in return value");
  }

  SystemPath::MakeDirectories(dir);
  SystemPath::MakeDirectories(dir + "/pcap/");
  SystemPath::MakeDirectories(dir + "/queueTraces/");
  SystemPath::MakeDirectories(dir + "/cwndTraces/");
  // 新增throughputTraces資料夾
  SystemPath::MakeDirectories(dir + "/throughputTraces/");

  // 為router安裝queue discipline
  Config::SetDefault(qdiscTypeId + "::MaxSize",
                     QueueSizeValue(QueueSize("38p")));

  // 安裝queue discipline在router的interface上
  TrafficControlHelper tch;
  tch.SetRootQueueDisc(qdiscTypeId);
  QueueDiscContainer qd;
  tch.Uninstall(routers.Get(0)->GetDevice(0));
  qd.Add(tch.Install(routers.Get(0)->GetDevice(0)).Get(0));

  // 設定queue discipline的queue limits為DynamicQueueLimits
  tch.SetQueueLimits("ns3::DynamicQueueLimits");

  // 開啟輸出檔案以儲存queue size與cwnd變化
  fPlotQueue.open(dir + "queue-size.dat", std::ios::out);
  fPlotCwnd.open(dir + "cwndTraces/n0.dat", std::ios::out);
  fPlotThroughput.open(dir + "throughputTraces/n0.dat", std::ios::out);

  // 追蹤queue discipline的queue size變化
  Simulator::ScheduleNow(&CheckQueueSize, qd.Get(0));

  AsciiTraceHelper asciiTraceHelper;
  Ptr<OutputStreamWrapper> streamWrapper;

  // 追蹤queue discipline的drop事件
  streamWrapper =
      asciiTraceHelper.CreateFileStream(dir + "/queueTraces/drop-0.dat");
  streamWrapper =
      asciiTraceHelper.CreateFileStream(dir + "/queueTraces/drop-0.dat");
  qd.Get(0)->TraceConnectWithoutContext(
      "Drop", MakeBoundCallback(&DropAtQueue, streamWrapper));

  // 安裝PacketSink應用程式在receiver node上
  uint16_t port = 50000;
  InstallPacketSink(rightNodes.Get(0), port, "ns3::TcpSocketFactory");

  // 安裝BulkSend應用程式在sender node上，並追蹤cwnd變化
  InstallBulkSend(leftNodes.Get(0), routerToRightIPAddress[0].GetAddress(1),
                  port, socketFactory, 2, 0, MakeCallback(&CwndChange));

  // 新增UDP流量，使用OnOffApplication模擬突發性UDP流量
  uint16_t udpPort = 50002; // 使用與 TCP 不同的 Port

  // 1. 安裝 UDP 接收端
  PacketSinkHelper udpSink("ns3::UdpSocketFactory",
                           InetSocketAddress(Ipv4Address::GetAny(), udpPort));
  ApplicationContainer udpSinkApps = udpSink.Install(rightNodes.Get(0));
  udpSinkApps.Start(Seconds(0.0));
  udpSinkApps.Stop(stopTime);

  // 2. 安裝 UDP 隨機發送端 (OnOffApplication)
  OnOffHelper udpSource(
      "ns3::UdpSocketFactory",
      InetSocketAddress(routerToRightIPAddress[0].GetAddress(1), udpPort));

  // 設定 UDP 傳輸速率與封包大小
  // 這裡設定 5Mbps，總頻寬(10Mbps)
  udpSource.SetAttribute("DataRate", StringValue("5Mbps"));
  udpSource.SetAttribute("PacketSize", UintegerValue(1024));

  // 3. 設定隨機的 On/Off 時間
  // 使用平均值為 0.5 秒的指數分佈，讓UDP不穩定干擾TCP。
  udpSource.SetAttribute(
      "OnTime", StringValue("ns3::ExponentialRandomVariable[Mean=0.5]"));
  udpSource.SetAttribute(
      "OffTime", StringValue("ns3::ExponentialRandomVariable[Mean=0.5]"));

  ApplicationContainer udpSourceApps = udpSource.Install(leftNodes.Get(0));

  // 讓 UDP 在 TCP 已經穩定運作後才「突襲」加入 (例如第 15 秒)
  udpSourceApps.Start(Seconds(15.0));
  udpSourceApps.Stop(stopTime);

  // 啟用pcap追蹤在所有point-to-point link上
  pointToPointLeaf.EnablePcapAll(dir + "pcap/ns-3", true);
  // 追蹤Throughput
  Simulator::Schedule(Seconds(0.000001), &TraceThroughput, monitor);

  Simulator::Stop(stopTime);
  Simulator::Run();

  // 將queue discipline的統計資訊寫入檔案
  std::ofstream myfile;
  myfile.open(dir + "queueStats.txt",
              std::fstream::in | std::fstream::out | std::fstream::app);
  myfile << std::endl;
  myfile << "Stat for Queue 1";
  myfile << qd.Get(0)->GetStats();
  myfile.close();

  // 將模擬配置儲存到檔案中
  myfile.open(dir + "config.txt",
              std::fstream::in | std::fstream::out | std::fstream::app);
  myfile << "qdiscTypeId " << qdiscTypeId << "\n";
  myfile << "stream  " << stream << "\n";
  myfile << "segmentSize " << segmentSize << "\n";
  myfile << "delAckCount " << delAckCount << "\n";
  myfile << "stopTime " << stopTime.As(Time::S) << "\n";
  myfile.close();

  Simulator::Destroy();

  fPlotQueue.close();
  fPlotCwnd.close();
  // 關閉新增的throughput輸出檔案
  fPlotThroughput.close();
  return 0;
}