<?php

$db = new PDO('mysql:host=docker;port=3307;dbname=kululasku_dev', 'kululasku_dev', 'RCaXGmS3Vv2NYFIy0qKR', array( PDO::ATTR_PERSISTENT => false));
$db->exec("set foreign_key_checks=0");
$tmpdb = new PDO('mysql:host=docker;port=3307;dbname=kululasku_tmp', 'kululasku_dev', 'RCaXGmS3Vv2NYFIy0qKR', array( PDO::ATTR_PERSISTENT => false));

$organisations = [];

$orphan_receipts = [];

$expensetypes = [];

$expensetype_mapping = [];

$expense_org_mapping = [];
try {
  $q = $tmpdb->prepare("SELECT * FROM yhrek_person");
  $q->execute();
  $rows = $q->fetchAll();
  $sql = "INSERT INTO expenseapp_person (id, iban, swift_bic, user_id, type) VALUES (?, ?, ?, ?, ?)";
  $stmt = $db->prepare($sql);
  foreach ($rows as $row) {
    $stmt->execute([$row['id'], $row['iban'], $row['swift'], $row['user_id'], 1]);
  }

  $q = $tmpdb->prepare("SELECT * FROM yhrek_organisation");
  $q->execute();
  $rows = $q->fetchAll();
  $sql = "INSERT INTO expenseapp_organisation (id, name, business_id, active, send_active) VALUES (?, ?, ?, ?, ?)";
  $stmt = $db->prepare($sql);
  foreach ($rows as $row) {
    $stmt->execute([$row['id'], $row['name'], '0000-0', 1, 0]);
    $organisations[] = $row['id'];
  }

  $q = $tmpdb->prepare("SELECT * FROM yhrek_expensetype");
  $q->execute();
  $rows = $q->fetchAll();
  $sql = "INSERT INTO expenseapp_expensetype (name, active, type, requires_receipt, multiplier, requires_endtime, account, unit, organisation_id, requires_start_time, persontype) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";
  $stmt = $db->prepare($sql);
  $etype_un = [
    1 => 'pcs',
    '*' => 'km'
  ];
  foreach ($rows as $row) {
    $expensetypes[$row['id']] = ['name' => $row['name'], 'type' => 'O', 'multiplier' => $row['multiplier']];
    foreach ($organisations as $org_id) {
      $data = [$row['name'], 1, 'O', 0, $row['multiplier'], 0, 0, $row['id'] == 1 ? 'pcs' : 'km', $org_id, 0, 1];
      $stmt->execute($data);
      $expensetype_mapping[$org_id][$row['id']] = $db->lastInsertId();
    }
  }

  $q = $tmpdb->prepare("SELECT * FROM yhrek_expense");
  $q->execute();
  $rows = $q->fetchAll();
  $cq = $tmpdb->prepare('SELECT date FROM yhrek_expenseevent WHERE expense_id = ? AND type = ? ORDER BY date ASC LIMIT 1');
  $uq = $tmpdb->prepare('SELECT date FROM yhrek_expenseevent WHERE expense_id = ? ORDER BY date DESC LIMIT 1');
  $sql = "INSERT INTO expenseapp_expense (id, name, email, phone, address, iban, swift_bic, personno, description, memo, status, katre_status, created_at, updated_at, organisation_id, user_id, workflow_id, num) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";
  $stmt = $db->prepare($sql);
  foreach ($rows as $row) {
    // Find from events.
    $cq->execute([$row['id'], 'R']);
    $created_at = $cq->fetchColumn();
    $uq->execute([$row['id']]);
    $updated_at = $uq->fetchColumn();
    $data = [$row['id'], $row['name'], $row['email'], '1234567890', 'Osoite puuttuu', $row['iban'], $row['swift'], '000000-0000', $row['description'], $row['notes'], 0, 1, $created_at, $updated_at, $row['organisation_id'], $row['sent_by_id'], $row['workflow_id'], $row['num']];
    $stmt->execute($data);
    $orphan_receipts[$row['id']] = $row['receipt'];
    $expense_org_mapping[$row['id']] = $row['organisation_id'];
  }

  $q = $tmpdb->prepare("SELECT * FROM yhrek_expenseline");
  $q->execute();
  $rows = $q->fetchAll();
  $sql = "INSERT INTO expenseapp_expenseline (id, description, begin_at, basis, receipt, expensetype_name, expensetype_type, multiplier, expense_id, expensetype_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";
  $stmt = $db->prepare($sql);
  foreach ($rows as $row) {
    // Find from events.
    $created_at = 0;
    $updated_at = 0;
    $expensetype = $expensetypes[$row['type_id']];
    if (isset($orphan_receipts[$row['expense_id']]) && empty($row['receipt'])) {
      $orphan_receipt = $orphan_receipts[$row['expense_id']];
      unset($orphan_receipts[$row['expense_id']]);
    }
    $expensetype_id = $expensetype_mapping[$expense_org_mapping[$row['expense_id']]][$row['type_id']];
    $stmt->execute([$row['id'], $row['description'], '1900-01-01', $row['basis'], isset($orphan_receipt) ? $orphan_receipt : $row['receipt'], $expensetype['name'], $expensetype['type'], $expensetype['multiplier'], $row['expense_id'], $expensetype_id]);
    $orphan_receipts[$row['id']] = $row['receipt'];
  }

  var_dump($orphan_receipts);
} catch(PDOException $e){
    die($e);
    return false;
}

