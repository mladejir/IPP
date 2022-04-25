<?php
ini_set('display_errors', 'stderr');

#definice konstant pro chyby
define("PARAM_ERR", 10);
define("HEADER_ERR", 21);
define("OPERATION_CODE_ERR", 22);
define("OTHER_ERR", 23);

//****************************************************************************************/
//                                   Pomocne funkce                                       /
//****************************************************************************************/

//Funkce pro vypis napovedy
function print_help(){
    echo "//*************** NAPOVEDA KE SKRIPTU parse.php **************//\n";
    echo "Ucel skriptu:\n";
    echo "Tento skript nacte ze standardniho vstupu zdrojovy kod v jazyce IPPcode22, zkontroluje lexikalni a syntaktickou spravnost kodu a vypise na standardni vystup XML reprezentaci programu. \n";
    echo "Pouziti skriptu:\n";
    echo "php8.1 parse.php [options] <vstupni_soubor >vystupni_soubor\n";
}

/**
 * Funkce na osetreni erroru
 * @param integer $line_num cislo radku
 * @param int $exit_num cislo ukonceni programu
 * @param string $error_msg Chybova zprava
 */ 
function print_error($line_num, $exit_num, $error_msg){
    if($line_num != -1){
        fprintf(STDERR, "Chyba na radku %d.\n", $line_num + 1);
    }
    fprintf(STDERR, "%s", $error_msg);
    exit($exit_num);
}

/**
 * Funkce pro XML vypis instrukce
 * @param mixed $xml xml objekt
 * @param int $order poradi instrukce
 * @param mixed $tokens tokeny programu 
 */ 
function print_instr_to_XML($xml, $order, $tokens){
    $xml->startElement('instruction');
    $xml->writeAttribute('order', $order);
    $xml->writeAttribute('opcode', $tokens[0]);
}

/**
 * Funkce pro XML vypis operandu
 * @param mixed $xml xml objekt
 * @param string $text pro XML atribut
 * @param string $arg_num cislo argumenty
 * @param string $type_str hodnota XML atributu
 */ 
function print_operand_to_XML($xml, $text, $arg_num, $type_str){
    $xml->startElement($arg_num);
    $xml->writeAttribute('type', $type_str);
    $xml->text($text);
    $xml->endElement();
}

//****************************************************************************************/
//                     Funkce pro kontrolu a zapis operandu instrukci                         /
//****************************************************************************************/

/**
 * Funkce pro zapis konstanty
 * @param mixed $xml objekt
 * @param mixed $sub_tokens sub_tokeny konstanty rozdelene podle '@'
 * @param int $line_num cislo radku
 * @param string $arg_str cislo argumentu
 * @param string $regex regularni vyraz, ktery musi vyhovovat
 */ 
function write_constant($xml, $sub_tokens, $line_num, $arg_str, $regex){

    $string_for_match = $sub_tokens[1]; //pro vsechny datove typy
    if($sub_tokens[0] == "string"){ //pro datovy typ string odstranim escape sekvence, kvuli pozdejsi kontrole, zda konstanta neobsahuje '\'
        $pattern = '/([\\\][\d]{3})/';
        $replacement = '';
        $string_for_match = preg_replace($pattern, $replacement, $sub_tokens[1]);
    }
    if($string_for_match == '' && $sub_tokens[0] == "string"){ //pokud je string prazdny
        $xml->startElement($arg_str);
        $xml->writeAttribute('type', $sub_tokens[0]);
        $xml->endElement();
    }
    else if(preg_match($regex, $string_for_match)){ 
        print_operand_to_XML($xml, $sub_tokens[1], $arg_str, $sub_tokens[0]);
    }
    else{
        print_error($line_num, OTHER_ERR, "Nevalidni konstanta!\n");
    }
}

/**
 * Funkce pro kontrolu a zapis promenne
 * @param mixed $xml objekt
 * @param mixed $tokens tokeny programu
 * @param int $line_num cislo radku
 * @param int $pos pozice promenne
 */ 
function is_var($tokens, $xml, $pos, $line_num){
    //vytvoreni elementu arg
    $arg_str = "arg";
    $arg_str = $arg_str . $pos;

    if(preg_match("/^(LF|TF|GF)@[a-zA-Z_\-\$&%\*!\?][\w\-\$&%\*!\?]*$/", $tokens[$pos])){
        print_operand_to_XML($xml, $tokens[$pos], $arg_str, "var");
    }
    else{
        print_error($line_num, OTHER_ERR, "Nevalidni promenna!\n");
    }
}

/**
 * Funkce pro rozliseni konstanty
 * @param mixed $xml objekt
 * @param mixed $sub_tokens sub_tokeny konstanty rozdelene podle '@'
 * @param int $line_num cislo radku
 * @param int $pos pozice promenne
 */ 
function is_constant($sub_tokens, $xml, $pos, $line_num){
    //vytvoreni elementu arg
    $arg_str = "arg";
    $arg_str = $arg_str . $pos;

    if($sub_tokens[0] == "nil"){
        write_constant($xml, $sub_tokens, $line_num, $arg_str, "/^nil$/");
    }
    else if($sub_tokens[0] == "bool"){
        write_constant($xml, $sub_tokens, $line_num, $arg_str, "/^(true|false)$/");
    }
    else if($sub_tokens[0] == "int"){
        write_constant($xml, $sub_tokens, $line_num, $arg_str, "/^[+-]?[0-9]+$/");
    }
    else if($sub_tokens[0] == "string"){
        write_constant($xml, $sub_tokens, $line_num, $arg_str, "/^[^\\\]+$/"); //nesmi byt \, 
    }
    else
    {
        print_error($line_num, OTHER_ERR, "Nevalidni datovy typ konstanty!\n");
    }
}

/**
 * Funkce pro kontrolu a zapis navesti
 * @param mixed $xml objekt
 * @param mixed $tokens tokeny programu
 * @param int $line_num cislo radku
 */ 
function is_label($tokens, $xml, $line_num){
    if(preg_match("/^[a-zA-Z_\-\$&%\*!\?][\w\-\$&%\*!\?]*$/", $tokens[1])){
        print_operand_to_XML($xml, $tokens[1], "arg1", "label");
    }
    else{
        print_error($line_num, OTHER_ERR, "Nevalidni navesti!\n");
    }
}

/**
 * Funkce pro rozliseni symbolu, zda se jedna o promennou nebo konstantu
 * @param mixed $xml objekt
 * @param mixed $tokens tokeny programu
 * @param int $line_num cislo radku
 * @param int $pos pozice promenne
 */ 
function is_symb($tokens, $xml, $pos, $line_num){
    $sub_tokens = explode("@", $tokens[$pos], 2);  //rozdeleni na substringy podle @
    if(count($sub_tokens) == 2){
        if($sub_tokens[0] == "GF" || $sub_tokens[0] == "LF" || $sub_tokens[0] == "TF"){
            is_var($tokens, $xml, $pos, $line_num);
        }
        else{
            is_constant($sub_tokens, $xml, $pos, $line_num);
        }
    }
    else{
        print_error($line_num, OTHER_ERR, "Nespravny tvar symbolu!\n");
    }
}

/**
 * Funkce pro kontrolu a zapis operandu <type>
 * @param mixed $xml objekt
 * @param mixed $tokens tokeny programu
 * @param int $line_num cislo radku
 */ 
function is_type($tokens, $xml, $line_num){
    if(preg_match("/^(nil|bool|int|string)$/", $tokens[2])){
        print_operand_to_XML($xml, $tokens[2], "arg2", "type");
    }
    else{
        print_error($line_num, OTHER_ERR, "Nevalidni datovy typ!\n");
    }
}

//****************************************************************************************/
//                              Funkce pro skupiny instrukci                              /
//****************************************************************************************/

/**
 * Funkce pro zapis instrukci, ktere nemaji operand
 * @param mixed $tokens tokeny programu (jednotliva slova)
 * @param mixed $xml xml objekt
 * @param int $order poradi instrukce
 * @param int $line_num cislo radku, na kterem je instrukce
 */ 
function empty_instr($tokens, $xml, $order, $line_num){
    if(count($tokens) != 1){
        print_error($line_num, OTHER_ERR, "Nespravny pocet operandu instrukce!\n");
    }
    print_instr_to_XML($xml, $order, $tokens);
}

//funkce pro instrukce, ktere maji operand <var>
function var_instr($tokens, $xml, $order, $line_num){
    if(count($tokens) != 2){
        print_error($line_num, OTHER_ERR, "Nespravny pocet operandu instrukce!\n");
    }
    print_instr_to_XML($xml, $order, $tokens);
    is_var($tokens, $xml, 1, $line_num);
}

//funkce pro instrukce, ktere maji operand <label>
function label_instr($tokens, $xml, $order, $line_num){
    if(count($tokens) != 2){
        print_error($line_num, OTHER_ERR, "Nespravny pocet operandu instrukce!\n");
    }
    print_instr_to_XML($xml, $order, $tokens);
    is_label($tokens, $xml, $line_num);
}

//funkce pro instrukce, ktere maji operand <symbol>
function symb_instr($tokens, $xml, $order, $line_num){
    if(count($tokens) != 2){
        print_error($line_num, OTHER_ERR, "Nespravny pocet operandu instrukce!\n");
    }
    print_instr_to_XML($xml, $order, $tokens);
    is_symb($tokens, $xml, 1, $line_num);
}

//funkce pro instrukce, ktere maji operandy <var> <symb>
function var_symb_instr($tokens, $xml, $order, $line_num){
    if(count($tokens) != 3){
        print_error($line_num, OTHER_ERR, "Nespravny pocet operandu instrukce!\n");
    }
    print_instr_to_XML($xml, $order, $tokens);
    is_var($tokens, $xml, 1, $line_num);
    is_symb($tokens, $xml, 2, $line_num);
}

//funkce pro instrukce, ktere maji operandy <var> <symb1> <symb2>
function var_2symb_instr($tokens, $xml, $order, $line_num){
    if(count($tokens) != 4){
        print_error($line_num, OTHER_ERR, "Nespravny pocet operandu instrukce!\n");
    }
    print_instr_to_XML($xml, $order, $tokens);
    is_var($tokens, $xml, 1, $line_num);
    is_symb($tokens, $xml, 2, $line_num);
    is_symb($tokens, $xml, 3, $line_num);
}                   

//funkce pro instrukce, ktere maji operandy <var> <type>
function var_type_instr($tokens, $xml, $order, $line_num){
    if(count($tokens) != 3){
        print_error($line_num, OTHER_ERR, "Nespravny pocet operandu instrukce!\n");
    }
    print_instr_to_XML($xml, $order, $tokens);
    is_var($tokens, $xml, 1, $line_num);
    is_type($tokens, $xml, $line_num);
}

//funkce pro instrukce, ktere maji operandy <label> <symb1> <symb2>
function label_2symb_instr($tokens, $xml, $order, $line_num){
    if(count($tokens) != 4){
        print_error($line_num, OTHER_ERR, "Nespravny pocet operandu instrukce!\n");
    }
    print_instr_to_XML($xml, $order, $tokens);
    is_label($tokens, $xml, $line_num);
    is_symb($tokens, $xml, 2, $line_num);
    is_symb($tokens, $xml, 3, $line_num);
}

//funkce pro kontrolu argumentu programu
function check_script_args($argc, $argv){
    if($argc > 1){
        if($argc == 2){
            if($argv[1] == "--help"){
                print_help();
                exit(0);
            }
            else{
                print_error(-1, PARAM_ERR, "Spatny argument programu!\n");
            }
        }
        else{
            print_error(-1, PARAM_ERR, "Spatny pocet argumentu programu!\n");
        }
    }
}


//****************************************************************************************/
//                                  HLAVNI TELO SKRIPTU                                   /
//****************************************************************************************/

//zpracovani argumentu programu
check_script_args($argc, $argv);

//zapsani dat pomoci XMLwriter
$xml = new XMLWriter();
$xml->openMemory();
$xml->startDocument('1.0', 'utf-8');
$xml->setIndent(true);
$xml->startElement('program');
$xml->writeAttribute('language', 'IPPcode22');

//odstranim z kazdeho radku komentare, bile znaky pred prvnim slovem a bile znaky navic za poslednim slovem
$lines = file("php://stdin");
for ($i = 0; $i < count($lines); $i++) {
    $pattern = '/#(.*)/';
    $replacement = '';
    $lines[$i] = preg_replace($pattern, $replacement, $lines[$i]);
    $lines[$i] = trim($lines[$i]);
}

$correct_header = false;    //promenna znacici spravny vyskyt hlavicky vstupniho souboru
$order = 0;                 //pocitadlo instrukci pro vypis ORDER
//hlavni smycka programu, kde postupne prochazim radky vstupu a zpracovavam "tokeny"
for ($i = 0; $i < count($lines); $i++) {
    //zajistim, aby se prochazely jen radky s nejakym obsahem
    if($lines[$i] != ''){
        //rozdelim na tokeny podle bilych znaku
        $tokens = preg_split('/\s+/', $lines[$i]);  
        //kontrola hlavicky 
        if(!$correct_header){
            if(strtoupper($tokens[0]) == ".IPPCODE22"){
                if(count($tokens) != 1){
                    print_error($i, HEADER_ERR, "Identifikator jazyka musi byt na radku sam!\n");
                }
                $correct_header = true;
            }
            else{
                print_error($i, HEADER_ERR, "Nevalidni struktura programu, na zacatku chybi hlavicka '.IPPcode22'\n");
            }
        }
        //zpracovani instrukci
        else
        {
            $tokens[0] = strtoupper($tokens[0]);
            $order++; //zvysim pocitadlo instrukci
            switch ($tokens[0]) {
                //bez operandu
                case "CREATEFRAME":
                case "PUSHFRAME":
                case "POPFRAME":
                case "RETURN":
                case "BREAK":
                    empty_instr($tokens, $xml, $order, $i);
                    break;
                // <var>
                case "DEFVAR":
                case "POPS":
                    var_instr($tokens, $xml, $order, $i);
                    break;
                //<label>
                case "CALL":
                case "LABEL":
                case "JUMP":
                    label_instr($tokens, $xml, $order, $i);
                    break;
                //<symb>
                case "PUSHS":
                case "WRITE":
                case "EXIT":
                case "DPRINT":
                    symb_instr($tokens, $xml, $order, $i);
                    break;
                //<var> <symb>
                case "MOVE":
                case "INT2CHAR":
                case "STRLEN":
                case "TYPE":
                case "NOT":
                    var_symb_instr($tokens, $xml, $order, $i);
                    break;
                //<var> <symb1> <symb2>
                case "ADD":
                case "SUB":
                case "MUL":
                case "IDIV":
                case "LT":
                case "GT":
                case "EQ":
                case "AND":
                case "OR":
                case "STRI2INT":
                case "CONCAT":
                case "GETCHAR":
                case "SETCHAR":
                    var_2symb_instr($tokens, $xml, $order, $i);
                    break;
                //<var> <type>
                case "READ":
                    var_type_instr($tokens, $xml, $order, $i);
                    break;
                //<label> <symb1> <symb2>
                case "JUMPIFEQ":
                case "JUMPIFNEQ":
                    label_2symb_instr($tokens, $xml, $order, $i);
                    break;
                default:
                    //token se s nicim neshoduje
                    print_error($i, OPERATION_CODE_ERR, "Neznama instrukce!\n");
                    break;
            }
            $xml->endElement();
        }
    }
}
//ukonceni vypisovaneho dokumentu
$xml->endElement();
$xml->endDocument();
//odstraneni implicitniho noveho radku na konci (ktery pridava XmlWriter) a zapsani na stdout
file_put_contents("php://output", trim($xml->outputMemory()));
$xml->flush();
?>