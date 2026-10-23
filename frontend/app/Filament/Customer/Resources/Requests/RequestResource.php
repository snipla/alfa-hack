<?php

namespace App\Filament\Customer\Resources\Requests;

use App\Filament\Customer\Resources\Requests\Pages\CreateRequest;
use App\Filament\Customer\Resources\Requests\Pages\EditRequest;
use App\Filament\Customer\Resources\Requests\Pages\ListRequests;
use App\Filament\Customer\Resources\Requests\Pages\ViewRequest;
use App\Filament\Customer\Resources\Requests\Schemas\RequestForm;
use App\Filament\Customer\Resources\Requests\Schemas\RequestInfolist;
use App\Filament\Customer\Resources\Requests\Tables\RequestsTable;
use App\Models\Request;
use BackedEnum;
use Filament\Resources\Resource;
use Filament\Schemas\Schema;
use Filament\Support\Icons\Heroicon;
use Filament\Tables\Table;

class RequestResource extends Resource
{
    protected static ?string $model = Request::class;

    protected static ?string $pluralModelLabel = 'Заявки на кредит';
    protected static string|BackedEnum|null $navigationIcon = Heroicon::OutlinedDocumentCheck;

    public static function form(Schema $schema): Schema
    {
        return RequestForm::configure($schema);
    }

    public static function infolist(Schema $schema): Schema
    {
        return RequestInfolist::configure($schema);
    }

    public static function table(Table $table): Table
    {
        return RequestsTable::configure($table);
    }

    public static function getRelations(): array
    {
        return [
            //
        ];
    }

    public static function getPages(): array
    {
        return [
            'index' => ListRequests::route('/'),
            'create' => CreateRequest::route('/create'),
            'view' => ViewRequest::route('/{record}'),
            'edit' => EditRequest::route('/{record}/edit'),
        ];
    }
}
